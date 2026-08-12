import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../i18n';

const HomePage: React.FC = () => {
  const { t } = useLanguage();

  return (
    <>
      <section className="section hero-content">
        <div className="container hero-inner">
          <div className="hero-text">
            <p className="eyebrow">Managers Desk</p>
            <h1>{t('Customer management', 'Kundenmanagement')}</h1>
            <p className="hero-subtitle">
              {t(
                'Manage customers, invoices, offers, and letters in one place. Keep everything organized and focus on what matters most.',
                'Kunden verwalten, Rechnungen, Angebote und Briefe an einem Ort. So behältst du den Überblick und kannst dich auf das Wesentliche konzentrieren.'
              )}
            </p>
            <div className="hero-actions">
              <Link to="/customers" className="btn btn-primary">
                {t('Customer overview', 'Kundenübersicht')}
              </Link>
              <Link to="/invoices" className="btn btn-secondary">
                {t('Invoices', 'Rechnungen')}
              </Link>
              <Link to="/offers" className="btn btn-secondary">
                {t('Offers', 'Angebote')}
              </Link>
              <Link to="/letters" className="btn btn-secondary">
                {t('Letters', 'Briefe')}
              </Link>
            </div>
            <ul className="hero-highlights">
              <li>{t('Create offers and invoices', 'Angebote & Rechnungen schreiben')}</li>
              <li>{t('Create and manage customers', 'Kunden anlegen & verwalten')}</li>
              <li>{t('Export as PDF in seconds', 'Ganz einfach als PDF exportieren')}</li>
            </ul>
          </div>
        </div>
      </section>
    </>
  );
};

export default HomePage;
