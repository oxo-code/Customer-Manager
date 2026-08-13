import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from docx2pdf import convert
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
LOCAL_DIR = BASE_DIR / ".local"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "output"
DIST_DIR = PROJECT_ROOT / "dist"
TEMPLATE_DIR = PROJECT_ROOT / "templates" / "docx"

LOCAL_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 14
JWT_ALGORITHM = "HS256"


def _get_auth_secret() -> str:
    env_secret = os.getenv("AUTH_SECRET_KEY")
    if env_secret:
        return env_secret

    secret_file = LOCAL_DIR / "auth_secret.key"
    if secret_file.exists():
        return secret_file.read_text(encoding="utf-8").strip()

    generated = secrets.token_urlsafe(48)
    secret_file.write_text(generated, encoding="utf-8")
    return generated


AUTH_SECRET_KEY = _get_auth_secret()


class RefreshRequestBody(schemas.AuthRefreshRequest):
    pass


class StatusUpdateBody(schemas.BaseModel):
    status: Literal["draft", "final"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except (UnknownHashError, ValueError, TypeError):
        # Backward compatibility: treat old plaintext records as legacy passwords.
        if not isinstance(plain_password, str) or not isinstance(password_hash, str):
            return False
        return secrets.compare_digest(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _create_token(payload: dict, expires_delta: timedelta) -> str:
    to_encode = payload.copy()
    to_encode["exp"] = _utcnow() + expires_delta
    return jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _create_access_token(user: models.User) -> str:
    return _create_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "type": "access",
        },
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def _store_refresh_token(db: Session, user: models.User) -> str:
    refresh_token = _create_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "type": "refresh",
            "jti": secrets.token_hex(16),
        },
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    db_token = models.RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=_utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)
    db.commit()
    return refresh_token


def _build_auth_response(db: Session, user: models.User) -> schemas.AuthTokenResponse:
    access_token = _create_access_token(user)
    refresh_token = _store_refresh_token(db, user)
    return schemas.AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=schemas.AuthUser.model_validate(user),
    )


def _decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.") from exc
    if payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
    return payload


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    payload = _decode_token(credentials.credentials, "access")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    return current_user


def _sanitize_filename(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in name)
    return safe or "upload.bin"


def _save_upload(file: UploadFile, prefix: str) -> str:
    original_name = _sanitize_filename(file.filename or "upload.bin")
    destination_name = f"{prefix}-{secrets.token_hex(6)}-{original_name}"
    destination = UPLOADS_DIR / destination_name
    content = file.file.read()
    destination.write_bytes(content)
    return f"/api/uploads/{destination_name}"


def _company_data(settings: Optional[models.CompanySettings]) -> dict:
    def _value(name: str, default: str = "") -> str:
        if settings is None:
            return default
        value = getattr(settings, name, default)
        return value if value is not None else default

    company_name = _value("company_name", "Customer Manager")
    full_name = _value("full_name", company_name)

    return {
        "name": company_name,
        "vollername": full_name,
        "adresse": _value("street"),
        "plz": _value("postal_code"),
        "ort": _value("city"),
        "land": _value("country"),
        "email": _value("email"),
        "telefon": _value("phone"),
        "logo": _value("document_logo_path") or _value("logo_path"),
    }


def build_invoice_context(invoice: models.Invoice, settings: Optional[models.CompanySettings]) -> dict:
    customer = invoice.customer
    total_netto = float(sum((item.total_price or 0.0) for item in invoice.items))
    vat_rate = 0.19
    total_brutto = total_netto * (1.0 + vat_rate)
    date_str = invoice.date.strftime("%Y-%m-%d") if invoice.date else ""

    return {
        "mandant": _company_data(settings),
        # Legacy + template-specific customer fields
        "customer_name": customer.name,
        "firma": customer.firma or "",
        "adresse": customer.adresse or "",
        "plz": customer.plz or "",
        "ort": customer.ort or "",
        "date": date_str,
        "customer_company": customer.firma,
        "customer_address": customer.adresse,
        "customer_zip": customer.plz,
        "customer_city": customer.ort,
        "invoice_number": invoice.invoice_number,
        "invoice_date": date_str,
        "items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in invoice.items
        ],
        "total_amount": invoice.total_amount,
        "total_netto": round(total_netto, 2),
        "mwst": round(vat_rate * 100, 2),
        "total_brutto": round(total_brutto, 2),
    }


def build_offer_context(offer: models.Offer, settings: Optional[models.CompanySettings]) -> dict:
    customer = offer.customer
    return {
        "mandant": _company_data(settings),
        "customer_name": customer.name,
        "customer_company": customer.firma,
        "customer_address": customer.adresse,
        "customer_zip": customer.plz,
        "customer_city": customer.ort,
        "offer_number": offer.offer_number,
        "offer_date": offer.date.strftime("%Y-%m-%d") if offer.date else "",
        "valid_until": offer.valid_until.strftime("%Y-%m-%d") if offer.valid_until else "",
        "items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in offer.items
        ],
        "total_amount": offer.total_amount,
    }


def build_letter_context(letter: models.Letter, settings: Optional[models.CompanySettings]) -> dict:
    customer = letter.customer
    return {
        "mandant": _company_data(settings),
        "customer_name": customer.name,
        "customer_company": customer.firma,
        "customer_address": customer.adresse,
        "customer_zip": customer.plz,
        "customer_city": customer.ort,
        "letter_id": letter.id,
        "letter_date": letter.date.strftime("%Y-%m-%d") if letter.date else "",
        "subject": letter.subject,
        "content": letter.content,
    }


def _first_existing_template(candidates: list[str]) -> Path:
    for name in candidates:
        template = TEMPLATE_DIR / name
        if template.exists():
            return template
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No suitable template file found.")


def _render_docx(template_path: Path, context: dict, output_filename: str) -> Path:
    output_path = OUTPUT_DIR / output_filename
    doc = DocxTemplate(str(template_path))

    rendered_context = context.copy()
    mandant = context.get("mandant") if isinstance(context, dict) else None
    if isinstance(mandant, dict):
        rendered_mandant = mandant.copy()
        logo_ref = rendered_mandant.get("logo")
        if isinstance(logo_ref, str) and logo_ref.startswith("/api/uploads/"):
            logo_name = _sanitize_filename(Path(logo_ref).name)
            logo_path = UPLOADS_DIR / logo_name
            if logo_path.exists() and logo_path.is_file():
                rendered_mandant["logo"] = InlineImage(doc, str(logo_path), width=Mm(32))
        rendered_context["mandant"] = rendered_mandant

    doc.render(rendered_context)
    doc.save(str(output_path))
    return output_path


def _convert_docx_to_pdf(docx_path: Path) -> Path:
    pdf_path = docx_path.with_suffix(".pdf")
    try:
        convert(str(docx_path), str(pdf_path))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF conversion failed. Ensure Microsoft Word is installed on Windows.",
        ) from exc
    if not pdf_path.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="PDF conversion produced no output file.")
    return pdf_path


app = FastAPI(title="Customer Manager API")


@app.get("/api/auth/bootstrap", response_model=schemas.AuthBootstrap)
def auth_bootstrap(db: Session = Depends(get_db)):
    user_count = db.query(models.User).count()
    return schemas.AuthBootstrap(setup_required=(user_count == 0))


@app.post("/api/auth/register-first", response_model=schemas.AuthTokenResponse)
def register_first_user(credentials: schemas.AuthCredentials, db: Session = Depends(get_db)):
    if db.query(models.User).count() > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Initial user already exists.")
    if len(credentials.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")

    username = credentials.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required.")

    user = models.User(username=username, password_hash=hash_password(credentials.password), role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_auth_response(db, user)


@app.post("/api/auth/login", response_model=schemas.AuthTokenResponse)
def login(credentials: schemas.AuthCredentials, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username.strip()).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    # Migrate old hashes (e.g. PBKDF2/plaintext) to current default bcrypt after successful login.
    try:
        if pwd_context.needs_update(user.password_hash):
            user.password_hash = hash_password(credentials.password)
            db.commit()
    except Exception:
        # Never block a valid login if hash-upgrade fails.
        db.rollback()

    return _build_auth_response(db, user)


@app.post("/api/auth/refresh", response_model=schemas.AuthTokenResponse)
def refresh_token(payload: RefreshRequestBody, db: Session = Depends(get_db)):
    refresh_token_value = payload.refresh_token
    decoded = _decode_token(refresh_token_value, "refresh")
    token_hash = hashlib.sha256(refresh_token_value.encode("utf-8")).hexdigest()

    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash).first()
    if db_token is None or db_token.revoked_at is not None or db_token.expires_at <= _utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired.")

    user_id = int(decoded.get("sub", "0"))
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    db_token.revoked_at = _utcnow()
    db.commit()

    return _build_auth_response(db, user)


@app.post("/api/auth/logout")
def logout(payload: RefreshRequestBody, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.refresh_token.encode("utf-8")).hexdigest()
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash).first()
    if db_token and db_token.user_id == current_user.id and db_token.revoked_at is None:
        db_token.revoked_at = _utcnow()
        db.commit()
    return {"ok": True}


@app.get("/api/auth/me", response_model=schemas.AuthUser)
def auth_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/api/auth/users", response_model=list[schemas.AuthUser])
def list_users(_: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.created_at.asc()).all()


@app.post("/api/auth/users", response_model=schemas.AuthUser)
def create_user(user_data: schemas.AuthCreateUser, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    username = user_data.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required.")
    if len(user_data.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists.")
    if user_data.role not in {"admin", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role.")

    user = models.User(username=username, password_hash=hash_password(user_data.password), role=user_data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.patch("/api/auth/users/{user_id}", response_model=schemas.AuthUser)
def update_user_role(user_id: int, payload: schemas.AuthUpdateUserRole, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if payload.role not in {"admin", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role.")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@app.delete("/api/auth/users/{user_id}")
def delete_user(user_id: int, current_admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account.")
    db.delete(user)
    db.commit()
    return {"ok": True}


@app.get("/api/customers", response_model=list[schemas.Customer])
def list_customers(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_customers(db)


@app.get("/api/customers/{customer_id}", response_model=schemas.Customer)
def get_customer(customer_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return customer


@app.post("/api/customers", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_customer(db, customer)


@app.put("/api/customers/{customer_id}", response_model=schemas.Customer)
def update_customer(customer_id: int, customer: schemas.CustomerCreate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = crud.update_customer(db, customer_id, customer)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return updated


@app.delete("/api/customers/{customer_id}")
def delete_customer(customer_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = crud.delete_customer(db, customer_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return {"ok": True}


@app.get("/api/invoices", response_model=list[schemas.Invoice])
def list_invoices(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_invoices(db)


@app.get("/api/invoices/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(invoice_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = crud.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return invoice


@app.post("/api/invoices/create", response_model=schemas.Invoice)
def create_invoice(invoice: schemas.InvoiceCreate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_invoice(db, invoice)


@app.patch("/api/invoices/{invoice_id}/status", response_model=schemas.Invoice)
def update_invoice_status(invoice_id: int, payload: StatusUpdateBody, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = crud.update_invoice_status(db, invoice_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return updated


@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = crud.delete_invoice(db, invoice_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return {"ok": True}


@app.get("/api/offers", response_model=list[schemas.Offer])
def list_offers(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_offers(db)


@app.get("/api/offers/{offer_id}", response_model=schemas.Offer)
def get_offer(offer_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer = crud.get_offer(db, offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return offer


@app.post("/api/offers/create", response_model=schemas.Offer)
def create_offer(offer: schemas.OfferCreate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_offer(db, offer)


@app.patch("/api/offers/{offer_id}/status", response_model=schemas.Offer)
def update_offer_status(offer_id: int, payload: StatusUpdateBody, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = crud.update_offer_status(db, offer_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return updated


@app.delete("/api/offers/{offer_id}")
def delete_offer(offer_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = crud.delete_offer(db, offer_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return {"ok": True}


@app.get("/api/letters", response_model=list[schemas.Letter])
def list_letters(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_letters(db)


@app.get("/api/letters/{letter_id}", response_model=schemas.Letter)
def get_letter(letter_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    letter = crud.get_letter(db, letter_id)
    if letter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Letter not found.")
    return letter


@app.post("/api/letters/create", response_model=schemas.Letter)
def create_letter(letter: schemas.LetterCreate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_letter(db, letter)


@app.get("/api/articles", response_model=list[schemas.Article])
def list_articles(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_articles(db)


@app.get("/api/articles/{article_id}", response_model=schemas.Article)
def get_article(article_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    article = crud.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
    return article


@app.post("/api/articles", response_model=schemas.Article)
def create_article(article: schemas.ArticleCreate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_article(db, article)


@app.put("/api/articles/{article_id}", response_model=schemas.Article)
def update_article(article_id: int, article: schemas.ArticleCreate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = crud.update_article(db, article_id, article)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
    return updated


@app.delete("/api/articles/{article_id}")
def delete_article(article_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = crud.delete_article(db, article_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
    return {"ok": True}


@app.get("/api/settings", response_model=schemas.CompanySettings)
def get_company_settings(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = crud.get_company_settings(db)
    if settings is None:
        settings = crud.update_company_settings(db, schemas.CompanySettingsUpdate())
    return settings


@app.put("/api/settings", response_model=schemas.CompanySettings)
def update_company_settings(payload: schemas.CompanySettingsUpdate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_company_settings(db, payload)


@app.post("/api/settings/logo", response_model=schemas.CompanySettings)
def upload_logo(file: UploadFile = File(...), _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logo_path = _save_upload(file, "company-logo")
    return crud.update_company_logo(db, logo_path, "logo_path")


@app.post("/api/settings/dark-logo", response_model=schemas.CompanySettings)
def upload_dark_logo(file: UploadFile = File(...), _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logo_path = _save_upload(file, "company-dark-logo")
    return crud.update_company_logo(db, logo_path, "dark_logo_path")


@app.post("/api/settings/document-logo", response_model=schemas.CompanySettings)
def upload_document_logo(file: UploadFile = File(...), _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logo_path = _save_upload(file, "company-document-logo")
    return crud.update_company_logo(db, logo_path, "document_logo_path")


@app.post("/api/documents/generate")
def generate_invoice_document(payload: schemas.DocumentGenerate, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = crud.get_invoice(db, payload.invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    settings = crud.get_company_settings(db)
    context = build_invoice_context(invoice, settings)
    template = _first_existing_template(["invoice_template.docx", "invoice_template_eng.docx"])
    safe_number = _sanitize_filename(invoice.invoice_number)
    out_path = _render_docx(template, context, f"invoice-{safe_number}.docx")
    return FileResponse(
        path=str(out_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=out_path.name,
    )


@app.post("/api/documents/generate-offer")
def generate_offer_document(payload: schemas.DocumentGenerateOffer, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer = crud.get_offer(db, payload.offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")

    settings = crud.get_company_settings(db)
    context = build_offer_context(offer, settings)
    template = _first_existing_template(["offer_template.docx", "offer_template_eng.docx"])
    safe_number = _sanitize_filename(offer.offer_number)
    out_path = _render_docx(template, context, f"offer-{safe_number}.docx")
    return FileResponse(
        path=str(out_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=out_path.name,
    )


@app.post("/api/documents/generate-letter")
def generate_letter_document(payload: schemas.DocumentGenerateLetter, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    letter = crud.get_letter(db, payload.letter_id)
    if letter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Letter not found.")

    settings = crud.get_company_settings(db)
    context = build_letter_context(letter, settings)
    template = _first_existing_template(["letter_template.docx", "letter_template_eng.docx", "briefvorlage.docx"])
    out_path = _render_docx(template, context, f"letter-{letter.id}.docx")
    return FileResponse(
        path=str(out_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=out_path.name,
    )


@app.get("/api/documents/download/{invoice_number}")
def download_invoice_docx(invoice_number: str, db: Session = Depends(get_db)):
    invoice = crud.get_invoice_by_number(db, invoice_number)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

    settings = crud.get_company_settings(db)
    context = build_invoice_context(invoice, settings)
    template = _first_existing_template(["invoice_template.docx", "invoice_template_eng.docx"])
    safe_number = _sanitize_filename(invoice.invoice_number)
    out_path = _render_docx(template, context, f"invoice-{safe_number}.docx")
    return FileResponse(
        path=str(out_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=out_path.name,
    )


@app.get("/api/documents/download-pdf/{invoice_number}")
def download_invoice_pdf(invoice_number: str, db: Session = Depends(get_db)):
    invoice = crud.get_invoice_by_number(db, invoice_number)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

    settings = crud.get_company_settings(db)
    context = build_invoice_context(invoice, settings)
    template = _first_existing_template(["invoice_template.docx", "invoice_template_eng.docx"])
    safe_number = _sanitize_filename(invoice.invoice_number)
    docx_path = _render_docx(template, context, f"invoice-{safe_number}.docx")
    pdf_path = _convert_docx_to_pdf(docx_path)
    return FileResponse(path=str(pdf_path), media_type="application/pdf", filename=pdf_path.name)


@app.get("/api/documents/download-offer/{offer_number}")
def download_offer_docx(offer_number: str, db: Session = Depends(get_db)):
    offer = crud.get_offer_by_number(db, offer_number)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")

    settings = crud.get_company_settings(db)
    context = build_offer_context(offer, settings)
    template = _first_existing_template(["offer_template.docx", "offer_template_eng.docx"])
    safe_number = _sanitize_filename(offer.offer_number)
    out_path = _render_docx(template, context, f"offer-{safe_number}.docx")
    return FileResponse(
        path=str(out_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=out_path.name,
    )


@app.get("/api/documents/download-offer-pdf/{offer_number}")
def download_offer_pdf(offer_number: str, db: Session = Depends(get_db)):
    offer = crud.get_offer_by_number(db, offer_number)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")

    settings = crud.get_company_settings(db)
    context = build_offer_context(offer, settings)
    template = _first_existing_template(["offer_template.docx", "offer_template_eng.docx"])
    safe_number = _sanitize_filename(offer.offer_number)
    docx_path = _render_docx(template, context, f"offer-{safe_number}.docx")
    pdf_path = _convert_docx_to_pdf(docx_path)
    return FileResponse(path=str(pdf_path), media_type="application/pdf", filename=pdf_path.name)


@app.get("/api/documents/download-letter-pdf/{letter_id}")
def download_letter_pdf(letter_id: int, db: Session = Depends(get_db)):
    letter = crud.get_letter(db, letter_id)
    if letter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Letter not found.")

    settings = crud.get_company_settings(db)
    context = build_letter_context(letter, settings)
    template = _first_existing_template(["letter_template.docx", "letter_template_eng.docx", "briefvorlage.docx"])
    docx_path = _render_docx(template, context, f"letter-{letter.id}.docx")
    pdf_path = _convert_docx_to_pdf(docx_path)
    return FileResponse(path=str(pdf_path), media_type="application/pdf", filename=pdf_path.name)


@app.get("/api/uploads/{filename}")
def serve_upload(filename: str):
    safe_name = _sanitize_filename(filename)
    file_path = UPLOADS_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return FileResponse(path=str(file_path))


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/", include_in_schema=False)
def root_index():
    if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
        return FileResponse(path=str(DIST_DIR / "index.html"))
    return {"message": "Customer Manager API is running."}


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if not DIST_DIR.exists() or not (DIST_DIR / "index.html").exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")

    candidate = DIST_DIR / full_path
    if candidate.exists() and candidate.is_file():
        return FileResponse(path=str(candidate))
    return FileResponse(path=str(DIST_DIR / "index.html"))