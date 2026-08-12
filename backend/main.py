from fastapi import FastAPI, Depends, File, HTTPException, UploadFile, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
import threading
import hashlib
import secrets
from uuid import uuid4
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from docx2pdf import convert
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from . import crud, models, schemas
from .database import RUNTIME_DIR, SessionLocal, engine
from .models import Customer, Invoice, InvoiceItem, Counter

models.Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    columns = {column[1] for column in connection.execute(text("PRAGMA table_info(company_settings)"))}
    if "dark_logo_path" not in columns:
        connection.execute(text("ALTER TABLE company_settings ADD COLUMN dark_logo_path VARCHAR"))
    if "full_name" not in columns:
        connection.execute(text("ALTER TABLE company_settings ADD COLUMN full_name VARCHAR"))
    if "document_logo_path" not in columns:
        connection.execute(text("ALTER TABLE company_settings ADD COLUMN document_logo_path VARCHAR"))

    user_table_exists = connection.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    ).fetchone()
    if user_table_exists:
        user_columns = {column[1] for column in connection.execute(text("PRAGMA table_info(users)"))}
        if "role" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
            connection.execute(text("UPDATE users SET role='admin' WHERE role IS NULL OR role=''"))

app = FastAPI(title="Customer Manager API")
PDF_CONVERSION_LOCK = threading.Lock()


def load_secret_key() -> str:
    env_secret = os.getenv("AUTH_SECRET_KEY")
    if env_secret:
        return env_secret

    secret_file = os.path.join(RUNTIME_DIR, "auth_secret.txt")
    os.makedirs(os.path.dirname(secret_file), exist_ok=True)

    if os.path.exists(secret_file):
        with open(secret_file, "r", encoding="utf-8") as file_handle:
            stored_secret = file_handle.read().strip()
            if stored_secret:
                return stored_secret

    generated_secret = secrets.token_urlsafe(64)
    with open(secret_file, "w", encoding="utf-8") as file_handle:
        file_handle.write(generated_secret)
    return generated_secret


SECRET_KEY = load_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_DAYS = 14
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "refresh",
        "exp": expire,
        "jti": uuid4().hex,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def store_refresh_token(db: Session, user_id: int, refresh_token: str):
    token_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_entry = models.RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(refresh_entry)
    db.commit()


def revoke_refresh_token(db: Session, refresh_token: str):
    token_hash = hash_refresh_token(refresh_token)
    entry = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash).first()
    if entry and entry.revoked_at is None:
        entry.revoked_at = datetime.now(timezone.utc)
        db.commit()


def issue_auth_tokens(db: Session, user):
    access_token = create_access_token(user.id, user.username)
    refresh_token = create_refresh_token(user.id, user.username)
    store_refresh_token(db, user.id, refresh_token)
    return schemas.AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=schemas.AuthUser.model_validate(user),
    )


def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        return None

    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_from_refresh_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        return None

    token_hash = hash_refresh_token(token)
    refresh_entry = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash).first()
    if refresh_entry is None:
        return None
    if refresh_entry.revoked_at is not None:
        return None
    expires_at = refresh_entry.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        return None

    return db.query(models.User).filter(models.User.id == user_id).first()


def require_admin(request: Request):
    if getattr(request.state, "user_role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")


def normalize_user_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in {"admin", "user"}:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'.")
    return normalized_role


def count_admin_users(db: Session) -> int:
    return db.query(models.User).filter(models.User.role == "admin").count()


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    if request.method == "OPTIONS":
        return await call_next(request)

    is_api = path.startswith("/api")
    is_public_auth = path in {
        "/api/auth/bootstrap",
        "/api/auth/login",
        "/api/auth/register-first",
        "/api/auth/refresh",
    }
    is_upload = path.startswith("/api/uploads")

    if not is_api or is_public_auth or is_upload:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    db = SessionLocal()
    try:
        user = get_user_from_token(token, db)
        if user is None:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})
        request.state.user_id = user.id
        request.state.username = user.username
        request.state.user_role = user.role
    finally:
        db.close()

    return await call_next(request)


def get_output_dir():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def build_company_template_context(settings):
    if settings is None:
        return {
            "name": "Customer Manager",
            "vollername": "Customer Manager",
            "adresse": "",
            "plz": "",
            "ort": "",
            "telefon": "",
            "email": "",
            "steuernr": "",
            "bank": "",
            "iban": "",
            "bic": "",
            "logo": "",
        }

    return {
        "name": settings.company_name or "Customer Manager",
        "vollername": settings.full_name or settings.company_name or "Customer Manager",
        "adresse": settings.street or "",
        "plz": settings.postal_code or "",
        "ort": settings.city or "",
        "telefon": settings.phone or "",
        "email": settings.email or "",
        "steuernr": settings.tax_number or "",
        "bank": settings.bank_name or "",
        "iban": settings.iban or "",
        "bic": settings.bic or "",
        "logo": settings.document_logo_path or settings.logo_path or settings.dark_logo_path or "",
    }


def resolve_logo_file_path(logo_value: str):
    if not logo_value:
        return None

    if logo_value.startswith("/api/uploads/"):
        file_name = os.path.basename(logo_value)
        candidate = os.path.join(UPLOADS_DIR, file_name)
        return candidate if os.path.exists(candidate) else None

    if os.path.isabs(logo_value) and os.path.exists(logo_value):
        return logo_value

    return None


def apply_logo_to_context(docx: DocxTemplate, context: dict):
    mandant = context.get("mandant")
    if not isinstance(mandant, dict):
        return

    logo_value = mandant.get("logo")
    if not isinstance(logo_value, str):
        mandant["logo"] = ""
        return

    logo_file_path = resolve_logo_file_path(logo_value)
    allowed_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff"}
    if logo_file_path and os.path.splitext(logo_file_path)[1].lower() in allowed_extensions:
        mandant["logo"] = InlineImage(docx, logo_file_path, width=Mm(36))
    else:
        mandant["logo"] = ""


def get_company_template_context(db: Session | None = None):
    settings = crud.get_company_settings(db) if db is not None else None
    return build_company_template_context(settings)


def build_invoice_context(invoice, company_settings):
    customer = invoice.customer
    items = invoice.items
    total_netto = invoice.total_amount
    mwst = total_netto * 0.19
    total_brutto = total_netto + mwst
    context = {
        "customer_name": customer.name,
        "firma": customer.firma or "",
        "adresse": customer.adresse,
        "plz": customer.plz,
        "ort": customer.ort,
        "email": customer.email or "",
        "telefon": customer.telefon or "",
        "invoice_number": invoice.invoice_number,
        "date": invoice.date.strftime("%d.%m.%Y") if hasattr(invoice.date, 'strftime') else str(invoice.date),
        "items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": f"{item.unit_price:.2f} €",
                "total_price": f"{item.total_price:.2f} €"
            } for item in items
        ],
        "total_netto": f"{total_netto:.2f} €",
        "mwst": f"{mwst:.2f} €",
        "total_brutto": f"{total_brutto:.2f} €",
        "mandant": build_company_template_context(company_settings),
    }

    return context


def build_offer_context(offer, company_settings):
    items = offer.items
    total_netto = offer.total_amount
    mwst = total_netto * 0.19
    total_brutto = total_netto + mwst
    context = {
        "customer": {
            "name": offer.customer.name,
            "firma": offer.customer.firma or "",
            "adresse": offer.customer.adresse,
            "plz": offer.customer.plz,
            "ort": offer.customer.ort,
            "email": offer.customer.email or "",
            "telefon": offer.customer.telefon or ""
        },
        "offer": {
            "number": offer.offer_number,
            "date": offer.date.strftime("%d.%m.%Y") if hasattr(offer.date, 'strftime') else str(offer.date),
            "valid_until": offer.valid_until.strftime("%d.%m.%Y") if offer.valid_until and hasattr(offer.valid_until, 'strftime') else (str(offer.valid_until) if offer.valid_until else ""),
            "total_netto": f"{total_netto:.2f} €",
            "mwst": f"{mwst:.2f} €",
            "total_brutto": f"{total_brutto:.2f} €"
        },
        "items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": f"{item.unit_price:.2f} €",
                "total_price": f"{item.total_price:.2f} €"
            } for item in items
        ],
        "total_netto": f"{total_netto:.2f} €",
        "mwst": f"{mwst:.2f} €",
        "total_brutto": f"{total_brutto:.2f} €",
        "mandant": build_company_template_context(company_settings),
    }

    return context


def build_letter_context(letter, company_settings):
    context = {
        "customer": {
            "name": letter.customer.name,
            "firma": letter.customer.firma or "",
            "adresse": letter.customer.adresse,
            "plz": letter.customer.plz,
            "ort": letter.customer.ort,
            "email": letter.customer.email or "",
            "telefon": letter.customer.telefon or ""
        },
        "letter": {
            "subject": letter.subject,
            "content": letter.content,
            "date": letter.date.strftime("%d.%m.%Y") if hasattr(letter.date, 'strftime') else str(letter.date)
        },
        "mandant": build_company_template_context(company_settings),
    }

    return context


# Funktion zur Konvertierung von DOCX zu PDF mit docx2pdf
def convert_docx_to_pdf(input_path: str, output_dir: str):
    input_path = os.path.abspath(input_path)
    output_dir = os.path.abspath(output_dir)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Die Datei {input_path} wurde nicht gefunden.")

    # Sicherstellen, dass das Ausgabeverzeichnis existiert
    os.makedirs(output_dir, exist_ok=True)

    # Zielpfad für die PDF-Datei
    output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
    temp_output_file = os.path.join(
        output_dir,
        f"{os.path.splitext(os.path.basename(input_path))[0]}_{uuid4().hex}.pdf",
    )

    def convert_via_word_com(source_path: str, target_path: str):
        import pythoncom
        import win32com.client

        word = None
        document = None
        pythoncom.CoInitialize()
        try:
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0

            document = word.Documents.Open(source_path)
            # 17 = wdExportFormatPDF
            document.ExportAsFixedFormat(target_path, 17)
        finally:
            if document is not None:
                document.Close(False)
            if word is not None:
                word.Quit()
            pythoncom.CoUninitialize()

    with PDF_CONVERSION_LOCK:
        try:
            convert(input_path, temp_output_file)

            if not os.path.exists(temp_output_file):
                raise RuntimeError("docx2pdf did not create a PDF file.")

            os.replace(temp_output_file, output_file)

            print(f"Die Datei wurde erfolgreich in {output_file} konvertiert.")
            return output_file
        except Exception as e:
            error_message = str(e).lower()
            if "invalid class string" in error_message or "ungültige klassenzeichenfolge" in error_message:
                raise RuntimeError(
                    "Microsoft Word wurde nicht gefunden oder ist nicht registriert. "
                    "docx2pdf benötigt eine lokal installierte Microsoft-Word-Desktopanwendung."
                ) from e

            # Fallback bei typischen COM/Word-Fehlern aus docx2pdf.
            # Der direkte COM-Export initialisiert COM explizit und ist robuster.
            if (
                "this command is not available" in error_message
                or "ausnahmefehler aufgetreten" in error_message
                or "coinitialize wurde nicht aufgerufen" in error_message
                or "coinitialize has not been called" in error_message
            ):
                try:
                    convert_via_word_com(input_path, temp_output_file)
                    if os.path.exists(temp_output_file):
                        os.replace(temp_output_file, output_file)
                        print(f"Die Datei wurde erfolgreich in {output_file} konvertiert.")
                        return output_file
                except Exception as fallback_error:
                    raise RuntimeError(
                        f"DOCX-zu-PDF-Konvertierung über Word COM fehlgeschlagen: {fallback_error}"
                    ) from fallback_error

            raise RuntimeError(
                f"DOCX-zu-PDF-Konvertierung mit docx2pdf fehlgeschlagen: {e}"
            ) from e
        finally:
            if os.path.exists(temp_output_file):
                try:
                    os.remove(temp_output_file)
                except OSError:
                    pass


def render_invoice_docx(invoice, db: Session | None = None):
    company_settings = crud.get_company_settings(db) if db is not None else None
    context = build_invoice_context(invoice, company_settings)
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "invoice_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template not found")

    docx = DocxTemplate(template_path)
    apply_logo_to_context(docx, context)
    docx.render(context)
    output_dir = get_output_dir()
    output_path = os.path.join(output_dir, f"invoice_{invoice.invoice_number}.docx")
    docx.save(output_path)
    return output_path


def render_offer_docx(offer, db: Session | None = None):
    company_settings = crud.get_company_settings(db) if db is not None else None
    context = build_offer_context(offer, company_settings)
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "offer_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Offer template not found")

    docx = DocxTemplate(template_path)
    apply_logo_to_context(docx, context)
    docx.render(context)
    output_dir = get_output_dir()
    output_path = os.path.join(output_dir, f"offer_{offer.offer_number}.docx")
    docx.save(output_path)
    return output_path


def render_letter_docx(letter, db: Session | None = None):
    company_settings = crud.get_company_settings(db) if db is not None else None
    context = build_letter_context(letter, company_settings)
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "briefvorlage.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Letter template not found")

    docx = DocxTemplate(template_path)
    apply_logo_to_context(docx, context)
    docx.render(context)
    output_dir = get_output_dir()
    output_path = os.path.join(output_dir, f"letter_{letter.id}.docx")
    docx.save(output_path)
    return output_path


@app.get("/api/auth/bootstrap", response_model=schemas.AuthBootstrap)
def auth_bootstrap(db: Session = Depends(get_db)):
    user_count = db.query(models.User).count()
    return schemas.AuthBootstrap(setup_required=user_count == 0)


@app.post("/api/auth/register-first", response_model=schemas.AuthTokenResponse)
def register_first_user(credentials: schemas.AuthCredentials, db: Session = Depends(get_db)):
    if db.query(models.User).count() > 0:
        raise HTTPException(status_code=403, detail="Initial setup already completed.")

    username = credentials.username.strip()
    if len(username) < 3 or len(credentials.password) < 8:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters and password at least 8 characters.")

    user = models.User(username=username, password_hash=hash_password(credentials.password), role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)

    return issue_auth_tokens(db, user)


@app.post("/api/auth/login", response_model=schemas.AuthTokenResponse)
def login(credentials: schemas.AuthCredentials, db: Session = Depends(get_db)):
    username = credentials.username.strip()
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return issue_auth_tokens(db, user)


@app.post("/api/auth/refresh", response_model=schemas.AuthTokenResponse)
def refresh_auth_token(payload: schemas.AuthRefreshRequest, db: Session = Depends(get_db)):
    user = get_user_from_refresh_token(payload.refresh_token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    revoke_refresh_token(db, payload.refresh_token)
    return issue_auth_tokens(db, user)


@app.post("/api/auth/logout")
def logout(payload: schemas.AuthRefreshRequest, request: Request, db: Session = Depends(get_db)):
    if getattr(request.state, "user_id", None) is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    revoke_refresh_token(db, payload.refresh_token)
    return {"message": "Logged out"}


@app.post("/api/auth/users", response_model=schemas.AuthUser)
def create_user(payload: schemas.AuthCreateUser, request: Request, db: Session = Depends(get_db)):
    require_admin(request)

    role = normalize_user_role(payload.role)

    username = payload.username.strip()
    if len(username) < 3 or len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters and password at least 8 characters.")

    exists = db.query(models.User).filter(models.User.username == username).first()
    if exists is not None:
        raise HTTPException(status_code=409, detail="Username already exists.")

    user = models.User(username=username, password_hash=hash_password(payload.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.AuthUser.model_validate(user)


@app.get("/api/auth/users", response_model=list[schemas.AuthUser])
def list_users(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    users = db.query(models.User).order_by(models.User.username.asc()).all()
    return [schemas.AuthUser.model_validate(user) for user in users]


@app.patch("/api/auth/users/{user_id}", response_model=schemas.AuthUser)
def update_user_role(user_id: int, payload: schemas.AuthUpdateUserRole, request: Request, db: Session = Depends(get_db)):
    require_admin(request)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    new_role = normalize_user_role(payload.role)
    if user.role == "admin" and new_role != "admin" and count_admin_users(db) <= 1:
        raise HTTPException(status_code=400, detail="At least one admin must remain.")

    user.role = new_role
    db.commit()
    db.refresh(user)
    return schemas.AuthUser.model_validate(user)


@app.delete("/api/auth/users/{user_id}")
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)

    current_user_id = getattr(request.state, "user_id", None)
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.role == "admin" and count_admin_users(db) <= 1:
        raise HTTPException(status_code=400, detail="At least one admin must remain.")

    db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@app.get("/api/auth/me", response_model=schemas.AuthUser)
def auth_me(request: Request, db: Session = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return schemas.AuthUser.model_validate(user)

@app.get("/api/settings", response_model=schemas.CompanySettings)
def read_company_settings(db: Session = Depends(get_db)):
    settings = crud.get_company_settings(db)
    if settings:
        return settings
    return schemas.CompanySettings(id=0, company_name="Customer Manager")

@app.put("/api/settings", response_model=schemas.CompanySettings)
def save_company_settings(settings: schemas.CompanySettingsUpdate, db: Session = Depends(get_db)):
    return crud.update_company_settings(db, settings)

async def save_logo(file: UploadFile, field_name: str, db: Session):
    extension = os.path.splitext(file.filename or "")[1].lower()
    if field_name == "document_logo_path":
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        allowed_content_types = {"image/jpeg", "image/png", "application/octet-stream"}
        error_detail = "Für Dokumente sind nur JPG oder PNG erlaubt."
    else:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
        allowed_content_types = {"image/jpeg", "image/png", "image/webp", "image/svg+xml", "application/octet-stream"}
        error_detail = "Nur JPG, PNG, WebP oder SVG sind erlaubt."

    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Ungültiges Bildformat.")
    if file.content_type and file.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail=error_detail)
    file_name = f"{field_name}-{uuid4().hex}{extension}"
    target_path = os.path.join(UPLOADS_DIR, file_name)
    with open(target_path, "wb") as target:
        shutil.copyfileobj(file.file, target)
    return crud.update_company_logo(db, f"/api/uploads/{file_name}", field_name)

@app.post("/api/settings/logo", response_model=schemas.CompanySettings)
async def upload_company_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await save_logo(file, "logo_path", db)

@app.post("/api/settings/dark-logo", response_model=schemas.CompanySettings)
async def upload_company_dark_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await save_logo(file, "dark_logo_path", db)

@app.post("/api/settings/document-logo", response_model=schemas.CompanySettings)
async def upload_document_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await save_logo(file, "document_logo_path", db)

@app.get("/api/customers", response_model=list[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    customers = crud.get_customers(db, skip=skip, limit=limit)
    return customers

@app.post("/api/customers", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db=db, customer=customer)

@app.get("/api/customers/{customer_id}", response_model=schemas.Customer)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@app.put("/api/customers/{customer_id}", response_model=schemas.Customer)
def update_customer(customer_id: int, customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = crud.update_customer(db, customer_id=customer_id, customer=customer)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@app.delete("/api/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = crud.delete_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}

@app.post("/api/invoices/create", response_model=schemas.Invoice)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    return crud.create_invoice(db=db, invoice=invoice)

@app.get("/api/invoices", response_model=list[schemas.Invoice])
def read_invoices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    invoices = crud.get_invoices(db, skip=skip, limit=limit)
    return invoices

@app.get("/api/invoices/{invoice_id}", response_model=schemas.Invoice)
def read_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@app.patch("/api/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, payload: dict, db: Session = Depends(get_db)):
    status = payload.get("status")
    if status not in {"draft", "final"}:
        raise HTTPException(status_code=400, detail="Status must be 'draft' or 'final'.")
    invoice = crud.update_invoice_status(db, invoice_id=invoice_id, status=status)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = crud.delete_invoice(db, invoice_id=invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": "Invoice deleted"}

@app.post("/api/offers/create", response_model=schemas.Offer)
def create_offer(offer: schemas.OfferCreate, db: Session = Depends(get_db)):
    return crud.create_offer(db=db, offer=offer)

@app.get("/api/offers", response_model=list[schemas.Offer])
def read_offers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    offers = crud.get_offers(db, skip=skip, limit=limit)
    return offers

@app.get("/api/offers/{offer_id}", response_model=schemas.Offer)
def read_offer(offer_id: int, db: Session = Depends(get_db)):
    db_offer = crud.get_offer(db, offer_id=offer_id)
    if db_offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    return db_offer

@app.patch("/api/offers/{offer_id}/status")
def update_offer_status(offer_id: int, payload: dict, db: Session = Depends(get_db)):
    status = payload.get("status")
    if status not in {"draft", "final"}:
        raise HTTPException(status_code=400, detail="Status must be 'draft' or 'final'.")
    offer = crud.update_offer_status(db, offer_id=offer_id, status=status)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer

@app.delete("/api/offers/{offer_id}")
def delete_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = crud.delete_offer(db, offer_id=offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    return {"message": "Offer deleted"}

@app.post("/api/letters/create", response_model=schemas.Letter)
def create_letter(letter: schemas.LetterCreate, db: Session = Depends(get_db)):
    return crud.create_letter(db=db, letter=letter)

@app.get("/api/letters", response_model=list[schemas.Letter])
def read_letters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    letters = crud.get_letters(db, skip=skip, limit=limit)
    return letters

@app.get("/api/letters/{letter_id}", response_model=schemas.Letter)
def read_letter(letter_id: int, db: Session = Depends(get_db)):
    db_letter = crud.get_letter(db, letter_id=letter_id)
    if db_letter is None:
        raise HTTPException(status_code=404, detail="Letter not found")
    return db_letter

@app.post("/api/documents/generate")
def generate_document(doc: schemas.DocumentGenerate, db: Session = Depends(get_db)):
    invoice = crud.get_invoice(db, invoice_id=doc.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    customer = invoice.customer
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    settings = crud.get_company_settings(db)
    context = build_invoice_context(invoice, settings)

    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "invoice_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template not found")

    docx = DocxTemplate(template_path)
    apply_logo_to_context(docx, context)
    docx.render(context)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"invoice_{invoice.invoice_number}.docx")
    docx.save(output_path)

    return {"message": "Document generated", "path": output_path, "download_url": f"/api/documents/download/{invoice.invoice_number}"}

@app.get("/api/documents/download/{invoice_number}")
def download_document(invoice_number: str):
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    file_name = f"invoice_{invoice_number}.docx"
    file_path = os.path.join(output_dir, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Invoice document not found")
    return FileResponse(path=file_path, filename=file_name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.get("/api/documents/download-offer/{offer_number}")
def download_offer_pdf(offer_number: str, db: Session = Depends(get_db)):
    offer = crud.get_offer_by_number(db, offer_number=offer_number)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Render the DOCX file
    docx_path = render_offer_docx(offer, db)
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=500, detail="Failed to generate DOCX file.")

    # Convert DOCX to PDF
    try:
        pdf_path = convert_docx_to_pdf(docx_path, get_output_dir())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail=f"PDF file not found at {pdf_path}.")

    return FileResponse(
        path=pdf_path,
        filename=os.path.basename(pdf_path),
        media_type="application/pdf"
    )

@app.get("/api/documents/download-pdf/{invoice_number}")
def download_invoice_pdf(invoice_number: str, db: Session = Depends(get_db)):
    invoice = crud.get_invoice_by_number(db, invoice_number=invoice_number)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Render the DOCX file
    docx_path = render_invoice_docx(invoice, db)
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=500, detail="Failed to generate DOCX file.")

    # Convert DOCX to PDF
    try:
        pdf_path = convert_docx_to_pdf(docx_path, get_output_dir())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail=f"PDF file not found at {pdf_path}.")

    return FileResponse(
        path=pdf_path,
        filename=os.path.basename(pdf_path),
        media_type="application/pdf"
    )

@app.post("/api/documents/generate-offer")
def generate_offer_document(doc: schemas.DocumentGenerateOffer, db: Session = Depends(get_db)):
    offer = crud.get_offer(db, offer_id=doc.offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    settings = crud.get_company_settings(db)
    context = build_offer_context(offer, settings)

    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "offer_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Offer template not found")

    docx = DocxTemplate(template_path)
    apply_logo_to_context(docx, context)
    docx.render(context)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"offer_{offer.offer_number}.docx")
    docx.save(output_path)

    return {"message": "Offer document generated", "path": output_path, "download_url": f"/api/documents/download-offer/{offer.offer_number}"}

@app.get("/api/documents/download-offer/{offer_number}")
def download_offer_document(offer_number: str):
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    file_name = f"offer_{offer_number}.docx"
    file_path = os.path.join(output_dir, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Offer document not found")
    return FileResponse(path=file_path, filename=file_name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.get("/api/documents/download-offer-pdf/{id}")
async def download_offer_pdf(id: str):
    try:
        # Generieren des Pfads zur PDF-Datei
        pdf_path = f"output/offer_{id}.pdf"

        # Überprüfen, ob die Datei existiert
        if not os.path.exists(pdf_path):
            # Wenn die Datei nicht existiert, versuchen, sie zu erstellen
            docx_path = f"output/offer_{id}.docx"
            if not os.path.exists(docx_path):
                raise HTTPException(status_code=404, detail=f"Die Quelldatei {docx_path} wurde nicht gefunden.")

            # Konvertierung von DOCX zu PDF
            try:
                convert_docx_to_pdf(docx_path, "output")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Fehler bei der PDF-Erstellung: {e}")

        # Rückgabe der Datei
        return FileResponse(path=pdf_path, filename=os.path.basename(pdf_path), media_type="application/pdf")
    except Exception as e:
        # Fehlerprotokollierung
        print(f"Fehler beim Herunterladen der Datei: {e}")
        raise HTTPException(status_code=500, detail="Ein interner Fehler ist aufgetreten.")

@app.post("/api/documents/generate-letter")
def generate_letter_document(doc: schemas.DocumentGenerateLetter, db: Session = Depends(get_db)):
    letter = crud.get_letter(db, letter_id=doc.letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    settings = crud.get_company_settings(db)
    context = build_letter_context(letter, settings)

    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "briefvorlage.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Letter template not found")

    docx = DocxTemplate(template_path)
    apply_logo_to_context(docx, context)
    docx.render(context)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"letter_{letter.id}.docx")
    docx.save(output_path)

    return {"message": "Letter document generated", "path": output_path, "download_url": f"/api/documents/download-letter/{letter.id}"}

@app.get("/api/documents/download-letter/{letter_id}")
def download_letter_document(letter_id: int):
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    file_name = f"letter_{letter_id}.docx"
    file_path = os.path.join(output_dir, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Letter document not found")
    return FileResponse(path=file_path, filename=file_name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.get("/api/documents/download-letter-pdf/{letter_id}")
def download_letter_pdf(letter_id: int, db: Session = Depends(get_db)):
    letter = crud.get_letter(db, letter_id=letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")

    # Render the DOCX file
    docx_path = render_letter_docx(letter)
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=500, detail="Failed to generate DOCX file.")

    # Convert DOCX to PDF
    try:
        pdf_path = convert_docx_to_pdf(docx_path, get_output_dir())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail=f"PDF file not found at {pdf_path}.")

    return FileResponse(
        path=pdf_path,
        filename=os.path.basename(pdf_path),
        media_type="application/pdf"
    )

@app.get("/api/articles", response_model=list[schemas.Article])
def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_articles(db, skip=skip, limit=limit)

@app.post("/api/articles", response_model=schemas.Article)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    return crud.create_article(db=db, article=article)

@app.get("/api/articles/{article_id}", response_model=schemas.Article)
def read_article(article_id: int, db: Session = Depends(get_db)):
    db_article = crud.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return db_article

@app.put("/api/articles/{article_id}", response_model=schemas.Article)
def update_article(article_id: int, article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    db_article = crud.update_article(db, article_id=article_id, article=article)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return db_article

@app.delete("/api/articles/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    db_article = crud.delete_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted"}