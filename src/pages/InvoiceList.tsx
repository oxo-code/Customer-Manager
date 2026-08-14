import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { deleteInvoice, getInvoices, getSignedDocumentDownloadUrl, updateInvoiceStatus } from '../services/api';
import { Invoice } from '../types/api';

const InvoiceList: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const { t, lang } = useLanguage();

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

  const finalizeInvoice = async (invoiceId: number) => {
    try {
      await updateInvoiceStatus(invoiceId, 'final');
      await loadInvoices();
    } catch (error) {
      console.error('Error finalizing invoice:', error);
      alert(t('The invoice could not be finalized.', 'Rechnung konnte nicht finalisiert werden.'));
    }
  };

  const removeInvoice = async (invoiceId: number) => {
    try {
      await deleteInvoice(invoiceId);
      await loadInvoices();
    } catch (error) {
      console.error('Error deleting invoice:', error);
      alert(t('The invoice could not be deleted.', 'Rechnung konnte nicht gelöscht werden.'));
    }
  };

  const getSignedUrl = async (kind: 'invoice_docx' | 'invoice_pdf', reference: string) => {
    return getSignedDocumentDownloadUrl({ kind, reference, lang });
  };

  const openDownload = async (kind: 'invoice_docx' | 'invoice_pdf', reference: string) => {
    try {
      const absoluteUrl = await getSignedUrl(kind, reference);
      window.open(absoluteUrl, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Download link generation failed', error);
      alert(t('The download link could not be generated.', 'Der Download-Link konnte nicht erzeugt werden.'));
    }
  };

  const sharePdf = async (reference: string, filename: string) => {
    const nav = navigator as any;
    const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent);

    try {
      const absoluteUrl = await getSignedUrl('invoice_pdf', reference);

      if (nav.share && isIos) {
        await nav.share({ url: absoluteUrl, title: filename, text: t('Share PDF', 'PDF teilen') });
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
        await nav.share({ url: absoluteUrl, title: filename, text: t('Share PDF', 'PDF teilen') });
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
          await nav.share({ url: absoluteUrl, title: filename, text: t('Share PDF', 'PDF teilen') });
          return;
        } catch {
          // fallback to download
        }
      }
      alert(t('Sharing failed. The PDF will be downloaded instead.', 'Teilen fehlgeschlagen. Die PDF wird heruntergeladen.'));
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
          <p className="eyebrow">{t('Invoices', 'Rechnungen')}</p>
          <h1 className="page-title">{t('Invoices', 'Rechnungen')}</h1>
          <p className="page-copy">{t('Overview of your invoices with status, amount, and customer assignment.', 'Übersicht deiner Rechnungen mit Status, Betrag und Kundenzuordnung.')}</p>
        </div>
        <Link to="/invoices/new" className="btn btn-primary">
          {t('New invoice', 'Neue Rechnung')}
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('Invoice No.', 'Rechnungs Nr.')}</th>
                <th>{t('Customer', 'Kunde')}</th>
                <th>{t('Date', 'Datum')}</th>
                <th>{t('Amount', 'Betrag')}</th>
                <th>{t('Status', 'Status')}</th>
                <th>{t('Download', 'Download')}</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(invoice => (
                <tr key={invoice.id}>
                  <td>{invoice.invoice_number}</td>
                  <td>{invoice.customer.name}</td>
                  <td>{new Date(invoice.date).toLocaleDateString()}</td>
                  <td>{invoice.total_amount} €</td>
                  <td>
                    <span className={`status status--${invoice.status}`}>
                      {invoice.status}
                    </span>
                  </td>
                  <td className="button-group">
                    {invoice.status === 'draft' && (
                      <>
                        <button
                          type="button"
                          className="btn btn-secondary btn-small"
                          onClick={() => finalizeInvoice(invoice.id)}
                        >
                          {t('Final', 'Final')}
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-small"
                          onClick={() => removeInvoice(invoice.id)}
                        >
                          {t('Delete', 'Löschen')}
                        </button>
                      </>
                    )}
                    <button
                      type="button"
                      className="btn btn-secondary btn-small btn-doc-action"
                      onClick={() => openDownload('invoice_docx', invoice.invoice_number)}
                    >
                      {t('Download Word', 'Word herunterladen')}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small btn-doc-action"
                      onClick={() => sharePdf(invoice.invoice_number, `${invoice.invoice_number}.pdf`)}
                    >
                      {t('Share PDF', 'PDF teilen')}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small btn-doc-action hide-on-mobile"
                      onClick={() => openDownload('invoice_pdf', invoice.invoice_number)}
                    >
                      {t('PDF direct link', 'PDF Direktlink')}
                    </button>
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