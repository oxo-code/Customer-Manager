import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { resolveApiUrl } from '../services/api';
import { deleteOffer, getOffers, updateOfferStatus } from '../services/api';
import { Offer } from '../types/api';

const OfferList: React.FC = () => {
  const [offers, setOffers] = useState<Offer[]>([]);
  const { t, lang } = useLanguage();

  useEffect(() => {
    loadOffers();
  }, []);

  const loadOffers = async () => {
    try {
      const response = await getOffers();
      setOffers(response.data.sort((a, b) => b.id - a.id));
    } catch (error) {
      console.error('Error loading offers:', error);
    }
  };

  const finalizeOffer = async (offerId: number) => {
    try {
      await updateOfferStatus(offerId, 'final');
      await loadOffers();
    } catch (error) {
      console.error('Error finalizing offer:', error);
      alert(t('The offer could not be finalized.', 'Angebot konnte nicht finalisiert werden.'));
    }
  };

  const removeOffer = async (offerId: number) => {
    try {
      await deleteOffer(offerId);
      await loadOffers();
    } catch (error) {
      console.error('Error deleting offer:', error);
      alert(t('The offer could not be deleted.', 'Angebot konnte nicht gelöscht werden.'));
    }
  };

  const sharePdf = async (url: string, filename: string) => {
    const nav = navigator as any;
    const absoluteUrl = resolveApiUrl(url);
    const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent);

    try {
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
          <p className="eyebrow">{t('Offers', 'Angebote')}</p>
          <h1 className="page-title">{t('Offers', 'Angebote')}</h1>
          <p className="page-copy">{t('Overview of your offers with status, amount, and customer assignment.', 'Übersicht deiner Angebote mit Status, Betrag und Kundenzuordnung.')}</p>
        </div>
        <Link to="/offers/new" className="btn btn-primary">
          {t('New offer', 'Neues Angebot')}
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('Offer No.', 'Angebotsnr.')}</th>
                <th>{t('Customer', 'Kunde')}</th>
                <th>{t('Date', 'Datum')}</th>
                <th>{t('Amount', 'Betrag')}</th>
                <th>{t('Status', 'Status')}</th>
                <th>{t('Download', 'Download')}</th>
              </tr>
            </thead>
            <tbody>
              {offers.map(offer => (
                <tr key={offer.id}>
                  <td>{offer.offer_number}</td>
                  <td>{offer.customer.name} {offer.customer.firma && `(${offer.customer.firma})`}</td>
                  <td>{new Date(offer.date).toLocaleDateString('de-DE')}</td>
                  <td>{offer.total_amount.toFixed(2)} €</td>
                  <td>
                    <span className={`status status--${offer.status}`}>
                      {offer.status}
                    </span>
                  </td>
                  <td className="button-group">
                    {offer.status === 'draft' && (
                      <>
                        <button
                          type="button"
                          className="btn btn-secondary btn-small"
                          onClick={() => finalizeOffer(offer.id)}
                        >
                          {t('Final', 'Final')}
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-small"
                          onClick={() => removeOffer(offer.id)}
                        >
                          {t('Delete', 'Löschen')}
                        </button>
                      </>
                    )}
                    <a
                      href={resolveApiUrl(`/api/documents/download-offer/${offer.offer_number}?lang=${encodeURIComponent(lang)}`)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-small btn-doc-action"
                    >
                      {t('Download Word', 'Word herunterladen')}
                    </a>
                    <a
                      href={resolveApiUrl(`/api/documents/download-offer-pdf/${offer.offer_number}?lang=${encodeURIComponent(lang)}`)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-small btn-doc-action hide-on-mobile"
                    >
                      {t('Direct link', 'Direktlink')}
                    </a>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small btn-doc-action"
                      onClick={() => sharePdf(`/api/documents/download-offer-pdf/${offer.offer_number}?lang=${encodeURIComponent(lang)}`, `${offer.offer_number}.pdf`)}
                    >
                      {t('Share', 'Teilen')}
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

export default OfferList;