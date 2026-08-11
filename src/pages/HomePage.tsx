import React, { useEffect, useRef } from 'react';
import anime from 'animejs';

const HomePage: React.FC = () => {

  return (
    <>


      <section className="section hero-content">
        <div className="container hero-inner">
          <div className="hero-text">
            <p className="eyebrow">Managers Desk</p>
            <h1>Kundenmanagement</h1>
            <p className="hero-subtitle">
              Kunden verwalten, Rechnungen, Angebote &amp; Briefe erstellen – alles an einem Ort. So behältst du den Überblick und kannst dich auf das Wesentliche konzentrieren.
            </p>
            <div className="hero-actions">
              <a href="/customers" className="btn btn-primary">
                Kundenübersicht
              </a>
              <a href="/invoices" className="btn btn-secondary">
                Rechnungen
              </a>
              <a href="/offers" className="btn btn-secondary">
                Angebote
              </a>
              <a href="/letters" className="btn btn-secondary">
                Briefe
              </a>
            </div>
            <ul className="hero-highlights">
              <li>Angebote & Rechnungen schreiben</li>
              <li>Kunden anlegen & verwalten</li>
              <li>Ganz einfach als PDF exportieren</li>
            </ul>
          </div>
        </div>
      </section>

      
    </>
  );
};

export default HomePage;
