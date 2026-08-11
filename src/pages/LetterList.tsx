import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getLetters } from '../services/api';
import { Letter } from '../types/api';

const LetterList: React.FC = () => {
  const [letters, setLetters] = useState<Letter[]>([]);

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
          <p className="eyebrow">Letters</p>
          <h1 className="page-title">Briefe</h1>
          <p className="page-copy">Übersicht deiner Briefe mit Betreff, Inhalt und Kundenzuordnung.</p>
        </div>
        <Link to="/letters/new" className="btn btn-primary">
          Neuer Brief
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Kunde</th>
                <th>Betreff</th>
                <th>Datum</th>
                <th>Download</th>
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
                      Direktlink
                    </a>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => sharePdf(`/api/documents/download-letter-pdf/${letter.id}`, `brief-${letter.id}.pdf`)}
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

export default LetterList;