import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getOffers } from '../services/api';
import { Offer } from '../types/api';

const OfferList: React.FC = () => {
  const [offers, setOffers] = useState<Offer[]>([]);

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
          <p className="eyebrow">Offers</p>
          <h1 className="page-title">Angebote</h1>
          <p className="page-copy">Übersicht deiner Angebote mit Status, Betrag und Kundenzuordnung.</p>
        </div>
        <Link to="/offers/new" className="btn btn-primary">
          Neues Angebot
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Angebotsnr.</th>
                <th>Kunde</th>
                <th>Datum</th>
                <th>Betrag</th>
                <th>Status</th>
                <th>Download</th>
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
                    <a
                      href={`/api/documents/download-offer/${offer.offer_number}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-small"
                    >
                      Download Word
                    </a>
                    <a
                      href={`/api/documents/download-offer-pdf/${offer.offer_number}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-small hide-on-mobile"
                    >
                      Direktlink
                    </a>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => sharePdf(`/api/documents/download-offer-pdf/${offer.offer_number}`, `${offer.offer_number}.pdf`)}
                    >
                      Teilen
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