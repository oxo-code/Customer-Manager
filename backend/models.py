from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    firma = Column(String, nullable=True)
    adresse = Column(Text)
    plz = Column(String)
    ort = Column(String)
    email = Column(String, nullable=True)
    telefon = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    invoice_number = Column(String, unique=True, index=True)
    date = Column(DateTime)
    total_amount = Column(Float)
    status = Column(String, default="draft")  # draft, sent, paid
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer")
    items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    total_price = Column(Float)

    invoice = relationship("Invoice", back_populates="items")

class Counter(Base):
    __tablename__ = "counters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    value = Column(Integer, default=1)

class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    offer_number = Column(String, unique=True, index=True)
    date = Column(DateTime)
    valid_until = Column(DateTime, nullable=True)
    total_amount = Column(Float)
    status = Column(String, default="draft")  # draft, sent, accepted, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer")
    items = relationship("OfferItem", back_populates="offer")

class OfferItem(Base):
    __tablename__ = "offer_items"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    description = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    total_price = Column(Float)

    offer = relationship("Offer", back_populates="items")

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    default_quantity = Column(Float, default=1.0)
    default_price = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Letter(Base):
    __tablename__ = "letters"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    subject = Column(String)
    content = Column(Text)
    date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer")

class CompanySettings(Base):
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True)
    company_name = Column(String, default="Customer Manager")
    full_name = Column(String, nullable=True)
    street = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    tax_number = Column(String, nullable=True)
    vat_id = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    bic = Column(String, nullable=True)
    logo_path = Column(String, nullable=True)
    dark_logo_path = Column(String, nullable=True)
    document_logo_path = Column(String, nullable=True)