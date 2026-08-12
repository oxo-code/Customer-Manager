import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { getLetters } from '../services/api';
import { Letter } from '../types/api';

const LetterList: React.FC = () => {
  const [letters, setLetters] = useState<Letter[]>([]);
  const { t } = useLanguage();

  useEffect(() => {
    loadLetters();
  }, []);

  const loadLetters = async () => {
    try {
      const response = await getLetters();
      setLetters(response.data.sort((a, b) => b.id - a.id));
    } catch (error) {
      console.error('Error loading letters:', error);
    }
  };

  const sharePdf = async (url: string, filename: string) => {
    const nav = navigator as any;
    const absoluteUrl = new URL(url, window.location.origin).toString();
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
          <p className="eyebrow">{t('Letters', 'Briefe')}</p>
          <h1 className="page-title">{t('Letters', 'Briefe')}</h1>
          <p className="page-copy">{t('Overview of your letters with subject, content, and customer assignment.', 'Übersicht deiner Briefe mit Betreff, Inhalt und Kundenzuordnung.')}</p>
        </div>
        <Link to="/letters/new" className="btn btn-primary">
          {t('New letter', 'Neuer Brief')}
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('Customer', 'Kunde')}</th>
                <th>{t('Subject', 'Betreff')}</th>
                <th>{t('Date', 'Datum')}</th>
                <th>{t('Download', 'Download')}</th>
              </tr>
            </thead>
            <tbody>
              {letters.map(letter => (
                <tr key={letter.id}>
                  <td>{letter.id}</td>
                  <td>{letter.customer.name} {letter.customer.firma && `(${letter.customer.firma})`}</td>
                  <td>{letter.subject}</td>
                  <td>{new Date(letter.date).toLocaleDateString('de-DE')}</td>
                  <td className="button-group">
                    <a
                      href={`/api/documents/download-letter-pdf/${letter.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-small hide-on-mobile"
                    >
                      {t('Direct link', 'Direktlink')}
                    </a>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => sharePdf(`/api/documents/download-letter-pdf/${letter.id}`, `brief-${letter.id}.pdf`)}
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

export default LetterList;