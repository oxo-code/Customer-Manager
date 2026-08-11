from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import subprocess
import pwd
import grp
from docxtpl import DocxTemplate
from datetime import datetime
from . import crud, models, schemas
from .database import SessionLocal, engine
from .models import Customer, Invoice, InvoiceItem, Counter

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
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


def get_output_dir():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# Funktion zur Konvertierung von DOCX zu PDF mit LibreOffice
def convert_docx_to_pdf(input_path: str, output_dir: str):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Die Datei {input_path} wurde nicht gefunden.")

    # Sicherstellen, dass das Ausgabeverzeichnis existiert
    os.makedirs(output_dir, exist_ok=True)

    # Zielpfad für die PDF-Datei
    output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")

    # Überprüfen, ob die Datei bereits existiert
    if os.path.exists(output_file):
        print(f"Die Datei {output_file} existiert bereits. Keine Konvertierung erforderlich.")
        return output_file

    try:
        # LibreOffice-Befehl ausführen
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", output_dir
        ], check=True)

        # Besitzrechte der Datei ändern
        current_user = pwd.getpwuid(os.getuid()).pw_name
        current_group = grp.getgrgid(os.getgid()).gr_name
        os.chown(output_file, os.getuid(), os.getgid())
        print(f"Besitzrechte der Datei {output_file} wurden auf {current_user}:{current_group} gesetzt.")

        print(f"Die Datei wurde erfolgreich in {output_file} konvertiert.")
        return output_file
    except Exception as e:
        print(f"Fehler bei der Konvertierung: {e}")
        return None


def render_invoice_docx(invoice):
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
        "total_brutto": f"{total_brutto:.2f} €"
    }
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "invoice_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template not found")

    docx = DocxTemplate(template_path)
    docx.render(context)
    output_dir = get_output_dir()
    output_path = os.path.join(output_dir, f"invoice_{invoice.invoice_number}.docx")
    docx.save(output_path)
    return output_path


def render_offer_docx(offer):
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
        "total_brutto": f"{total_brutto:.2f} €"
    }
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "offer_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Offer template not found")

    docx = DocxTemplate(template_path)
    docx.render(context)
    output_dir = get_output_dir()
    output_path = os.path.join(output_dir, f"offer_{offer.offer_number}.docx")
    docx.save(output_path)
    return output_path


def render_letter_docx(letter):
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
        }
    }
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "briefvorlage.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Letter template not found")

    docx = DocxTemplate(template_path)
    docx.render(context)
    output_dir = get_output_dir()
    output_path = os.path.join(output_dir, f"letter_{letter.id}.docx")
    docx.save(output_path)
    return output_path

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
        "total_brutto": f"{total_brutto:.2f} €"
    }

    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "invoice_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template not found")

    docx = DocxTemplate(template_path)
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
    docx_path = render_offer_docx(offer)
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
    docx_path = render_invoice_docx(invoice)
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
            "date": offer.date.strftime("%d.%m.%Y"),
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
        "total_brutto": f"{total_brutto:.2f} €"
    }

    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "offer_template.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Offer template not found")

    docx = DocxTemplate(template_path)
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
            "date": letter.date.strftime("%d.%m.%Y")
        }
    }

    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "docx", "briefvorlage.docx")
    template_path = os.path.abspath(template_path)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Letter template not found")

    docx = DocxTemplate(template_path)
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