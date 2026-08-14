import unittest
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import crud, models
from backend.main import build_invoice_context


class DocumentGenerationContextTest(unittest.TestCase):
    def test_invoice_context_includes_mandant_data(self):
        settings = SimpleNamespace(
            company_name='Beispiel Firma',
            street='Musterweg 7',
            postal_code='10115',
            city='Berlin',
            country='Deutschland',
            email='info@example.com',
            phone='+49 30 123456',
            logo_path='/api/uploads/company-logo.svg',
        )
        customer = SimpleNamespace(
            name='Max Mustermann',
            firma='Muster GmbH',
            adresse='Hauptstraße 1',
            plz='20095',
            ort='Hamburg',
            email='max@example.com',
            telefon='0123 456',
        )
        invoice = SimpleNamespace(
            customer=customer,
            invoice_number='2026-001',
            date=datetime(2026, 1, 15),
            total_amount=100.0,
            items=[
                SimpleNamespace(
                    description='Beratung',
                    quantity=1,
                    unit_price=80.0,
                    total_price=80.0,
                ),
                SimpleNamespace(
                    description='Material',
                    quantity=1,
                    unit_price=20.0,
                    total_price=20.0,
                ),
            ],
        )

        context = build_invoice_context(invoice, settings)

        self.assertEqual(context['mandant']['name'], 'Beispiel Firma')
        self.assertEqual(context['mandant']['vollername'], 'Beispiel Firma')
        self.assertEqual(context['mandant']['adresse'], 'Musterweg 7')
        self.assertEqual(context['mandant']['plz'], '10115')
        self.assertEqual(context['mandant']['ort'], 'Berlin')
        self.assertEqual(context['mandant']['telefon'], '+49 30 123456')
        self.assertEqual(context['mandant']['logo'], '/api/uploads/company-logo.svg')
        self.assertEqual(context['customer_name'], 'Max Mustermann')
        self.assertEqual(context['invoice_number'], '2026-001')
        self.assertEqual(context['total_netto'], 100.0)
        self.assertEqual(context['mwst'], 19.0)
        self.assertEqual(context['mwst_satz'], 19.0)
        self.assertEqual(context['total_brutto'], 119.0)

    def test_status_can_be_advanced_to_final_and_draft_can_be_deleted(self):
        engine = create_engine('sqlite:///:memory:')
        models.Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        customer = models.Customer(
            name='Max Mustermann',
            firma='Muster GmbH',
            adresse='Hauptstr. 1',
            plz='10115',
            ort='Berlin',
            email='max@example.com',
            telefon='1234',
        )
        session.add(customer)
        session.commit()
        session.refresh(customer)

        invoice = models.Invoice(
            customer_id=customer.id,
            invoice_number='2026-099',
            date=datetime(2026, 1, 15),
            total_amount=120.0,
            status='draft',
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)

        updated_invoice = crud.update_invoice_status(session, invoice.id, 'final')
        self.assertEqual(updated_invoice.status, 'final')

        deleted = crud.delete_invoice(session, invoice.id)
        self.assertIsNotNone(deleted)
        self.assertIsNone(crud.get_invoice(session, invoice.id))

        offer = models.Offer(
            customer_id=customer.id,
            offer_number='2026-099',
            date=datetime(2026, 1, 20),
            total_amount=75.0,
            status='draft',
        )
        session.add(offer)
        session.commit()
        session.refresh(offer)

        updated_offer = crud.update_offer_status(session, offer.id, 'final')
        self.assertEqual(updated_offer.status, 'final')

        deleted_offer = crud.delete_offer(session, offer.id)
        self.assertIsNotNone(deleted_offer)
        self.assertIsNone(crud.get_offer(session, offer.id))

        session.close()


if __name__ == '__main__':
    unittest.main()
