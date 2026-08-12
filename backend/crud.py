from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas

def get_company_settings(db: Session):
    return db.query(models.CompanySettings).first()

def update_company_settings(db: Session, settings: schemas.CompanySettingsUpdate):
    db_settings = get_company_settings(db)
    if not db_settings:
        db_settings = models.CompanySettings()
        db.add(db_settings)
    for key, value in settings.dict().items():
        setattr(db_settings, key, value)
    db.commit()
    db.refresh(db_settings)
    return db_settings

def update_company_logo(db: Session, logo_path: str, field_name: str = "logo_path"):
    db_settings = get_company_settings(db)
    if not db_settings:
        db_settings = models.CompanySettings()
        db.add(db_settings)
    setattr(db_settings, field_name, logo_path)
    db.commit()
    db.refresh(db_settings)
    return db_settings

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer(db: Session, customer_id: int, customer: schemas.CustomerCreate):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer:
        for key, value in customer.dict().items():
            setattr(db_customer, key, value)
        db.commit()
        db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer:
        db.delete(db_customer)
        db.commit()
    return db_customer


def update_invoice_status(db: Session, invoice_id: int, status: str):
    if status not in {"draft", "final"}:
        raise ValueError("Status must be either 'draft' or 'final'.")
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if db_invoice is None:
        return None
    db_invoice.status = status
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


def delete_invoice(db: Session, invoice_id: int):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if db_invoice is None:
        return None
    db.delete(db_invoice)
    db.commit()
    return db_invoice


def update_offer_status(db: Session, offer_id: int, status: str):
    if status not in {"draft", "final"}:
        raise ValueError("Status must be either 'draft' or 'final'.")
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if db_offer is None:
        return None
    db_offer.status = status
    db.commit()
    db.refresh(db_offer)
    return db_offer


def delete_offer(db: Session, offer_id: int):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if db_offer is None:
        return None
    db.delete(db_offer)
    db.commit()
    return db_offer


def get_next_invoice_number(db: Session):
    counter = db.query(models.Counter).filter(models.Counter.name == "invoice").with_for_update().first()
    if not counter:
        counter = models.Counter(name="invoice", value=1)
        db.add(counter)
        db.flush()  # Use flush instead of commit
    number = counter.value
    counter.value += 1
    return f"{datetime.now().year}-{number:03d}"

def create_invoice(db: Session, invoice: schemas.InvoiceCreate):
    invoice_number = get_next_invoice_number(db)
    total_amount = sum(item.quantity * item.unit_price for item in invoice.items)
    
    db_invoice = models.Invoice(
        customer_id=invoice.customer_id,
        invoice_number=invoice_number,
        date=invoice.date,
        total_amount=total_amount,
        status="draft"
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    for item in invoice.items:
        db_item = models.InvoiceItem(
            invoice_id=db_invoice.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price
        )
        db.add(db_item)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_invoices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Invoice).offset(skip).limit(limit).all()

def get_invoice(db: Session, invoice_id: int):
    return db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()

def get_invoice_by_number(db: Session, invoice_number: str):
    return db.query(models.Invoice).filter(models.Invoice.invoice_number == invoice_number).first()

def get_next_offer_number(db: Session):
    counter = db.query(models.Counter).filter(models.Counter.name == "offer").with_for_update().first()
    if not counter:
        counter = models.Counter(name="offer", value=1)
        db.add(counter)
        db.flush()
    number = counter.value
    counter.value += 1
    return f"{datetime.now().year}-{number:03d}"

def create_offer(db: Session, offer: schemas.OfferCreate):
    offer_number = get_next_offer_number(db)
    total_amount = sum(item.quantity * item.unit_price for item in offer.items)
    
    db_offer = models.Offer(
        customer_id=offer.customer_id,
        offer_number=offer_number,
        date=offer.date,
        valid_until=offer.valid_until,
        total_amount=total_amount,
        status="draft"
    )
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    
    for item in offer.items:
        db_item = models.OfferItem(
            offer_id=db_offer.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price
        )
        db.add(db_item)
    db.commit()
    db.refresh(db_offer)
    return db_offer

def get_offers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Offer).offset(skip).limit(limit).all()

def get_offer(db: Session, offer_id: int):
    return db.query(models.Offer).filter(models.Offer.id == offer_id).first()

def get_offer_by_number(db: Session, offer_number: str):
    return db.query(models.Offer).filter(models.Offer.offer_number == offer_number).first()

def create_letter(db: Session, letter: schemas.LetterCreate):
    db_letter = models.Letter(**letter.dict())
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    return db_letter

def get_letters(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Letter).offset(skip).limit(limit).all()

def get_letter(db: Session, letter_id: int):
    return db.query(models.Letter).filter(models.Letter.id == letter_id).first()

def get_articles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Article).offset(skip).limit(limit).all()

def get_article(db: Session, article_id: int):
    return db.query(models.Article).filter(models.Article.id == article_id).first()

def create_article(db: Session, article: schemas.ArticleCreate):
    db_article = models.Article(**article.dict())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def update_article(db: Session, article_id: int, article: schemas.ArticleCreate):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if db_article:
        for key, value in article.dict().items():
            setattr(db_article, key, value)
        db.commit()
        db.refresh(db_article)
    return db_article

def delete_article(db: Session, article_id: int):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if db_article:
        db.delete(db_article)
        db.commit()
    return db_article