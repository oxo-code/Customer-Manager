import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getInvoices } from '../services/api';
import { Invoice } from '../types/api';

const InvoiceList: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      const response = await getInvoices();
      setInvoices(response.data.sort((a, b) => b.id - a.id));
    } catch (error) {
      console.error('Error loading invoices:', error);
    }
  };

  const sharePdf = async (url: string, filename: string) => {
    const nav = navigator as any;
    const absoluteUrl = new URL(url, window.location.origin).toString();
    const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent);

    try {
      if (nav.share && isIos) {
        await nav.share({ url: absoluteUrl, title: filename, text: 'PDF teilen' });
        return;
      }

      const response = await fetch(absoluteUrl);
      if (!response.ok) throw new Error('PDF konnte nicht geladen werden');
      const blob = await response.blob();
      const file = new File([blob], filename, { type: blob.type || 'application/pdf' });

      if (!isIos && nav.share && nav.canShare && nav.canShare({ files: [file] })) {
        await nav.share({ files: [file], title: filename });
        return;
      }

      if (nav.share) {
        await nav.share({ url: absoluteUrl, title: filename, text: 'PDF teilen' });
        return;
      }

      const link = document.createElement('a');
      link.href = URL.createObjectURL(file);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    } catch (error) {
      console.error('Share failed', error);
      if (nav.share) {
        try {
          await nav.share({ url: absoluteUrl, title: filename, text: 'PDF teilen' });
          return;
        } catch {
          // fallback to download
        }
      }
      alert('Teilen fehlgeschlagen. Die PDF wird heruntergeladen.');
      const link = document.createElement('a');
      link.href = absoluteUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <main className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Invoices</p>
          <h1 className="page-title">Rechnungen</h1>
          <p className="page-copy">Übersicht deiner Rechnungen mit Status, Betrag und Kundenzuordnung.</p>
        </div>
        <Link to="/invoices/new" className="btn btn-primary">
          Neue Rechnung
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rechnungs Nr.</th>
                <th>Kunde</th>
                <th>Datum</th>
                <th>Betrag</th>
                <th>Status</th>
                <th>Download</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(invoice => (
                <tr key={invoice.id}>
                  <td>{invoice.invoice_number}</td>
                  <td>{invoice.customer.name}</td>
                  <td>{new Date(invoice.date).toLocaleDateString()}</td>
                  <td>{invoice.total_amount} €</td>
                  <td>{invoice.status}</td>
                  <td className="button-group">
                    <a
                      href={`/api/documents/download/${invoice.invoice_number}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary"
                    >
                      Download Word
                    </a>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => sharePdf(`/api/documents/download-pdf/${invoice.invoice_number}`, `${invoice.invoice_number}.pdf`)}
                    >
                      PDF Teilen
                    </button>
                    <a
                      href={`/api/documents/download-pdf/${invoice.invoice_number}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary btn-small hide-on-mobile"
                    >
                      PDF Direktlink
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
};

export default InvoiceList;