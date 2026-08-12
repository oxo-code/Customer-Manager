from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class CustomerBase(BaseModel):
    name: str
    firma: Optional[str] = None
    adresse: str
    plz: str
    ort: str
    email: Optional[str] = None
    telefon: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceItemBase(BaseModel):
    description: str
    quantity: float
    unit_price: float

class InvoiceItem(InvoiceItemBase):
    id: int
    invoice_id: int
    total_price: float

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    customer_id: int
    date: datetime
    items: List[InvoiceItemBase]

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: int
    invoice_number: str
    total_amount: float
    status: str
    created_at: datetime
    customer: Customer

    class Config:
        from_attributes = True

class DocumentGenerate(BaseModel):
    invoice_id: int

class OfferItemBase(BaseModel):
    description: str
    quantity: float
    unit_price: float

class OfferItem(OfferItemBase):
    id: int
    offer_id: int
    total_price: float

    class Config:
        from_attributes = True

class OfferBase(BaseModel):
    customer_id: int
    date: datetime
    valid_until: Optional[datetime] = None
    items: List[OfferItemBase]

class OfferCreate(OfferBase):
    pass

class Offer(OfferBase):
    id: int
    offer_number: str
    total_amount: float
    status: str
    valid_until: Optional[datetime] = None
    created_at: datetime
    customer: Customer

    class Config:
        from_attributes = True

class LetterBase(BaseModel):
    customer_id: int
    subject: str
    content: str
    date: datetime

class LetterCreate(LetterBase):
    pass

class Letter(LetterBase):
    id: int
    created_at: datetime
    customer: Customer

    class Config:
        from_attributes = True

class DocumentGenerateOffer(BaseModel):
    offer_id: int

class DocumentGenerateLetter(BaseModel):
    letter_id: int

class ArticleBase(BaseModel):
    name: str
    description: Optional[str] = None
    default_quantity: float = 1.0
    default_price: float = 0.0

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CompanySettingsBase(BaseModel):
    company_name: str = "Customer Manager"
    full_name: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_number: Optional[str] = None
    vat_id: Optional[str] = None
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None

class CompanySettingsUpdate(CompanySettingsBase):
    pass

class CompanySettings(CompanySettingsBase):
    id: int
    logo_path: Optional[str] = None
    dark_logo_path: Optional[str] = None
    document_logo_path: Optional[str] = None

    class Config:
        from_attributes = True