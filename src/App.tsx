import React, { useEffect, useState } from 'react';
import { Routes, Route, Link, NavLink, useLocation } from 'react-router-dom';
import HomePage from './pages/HomePage';
import CustomerList from './pages/CustomerList';
import CustomerForm from './pages/CustomerForm';
import InvoiceList from './pages/InvoiceList';
import InvoiceForm from './pages/InvoiceForm';
import OfferList from './pages/OfferList';
import OfferForm from './pages/OfferForm';
import LetterList from './pages/LetterList';
import LetterForm from './pages/LetterForm';
import ArticleList from './pages/ArticleList';
import ArticleForm from './pages/ArticleForm';
import SettingsPage from './pages/SettingsPage';
import AuthPage from './pages/AuthPage';
import { clearAuthToken, getAuthToken, getCompanySettings, getCurrentUser, getRefreshToken, logoutUser } from './services/api';
import { useLanguage } from './i18n';
import { AuthUser } from './types/api';

const App: React.FC = () => {
  const location = useLocation();
  const isHome = location.pathname === '/';
  const { lang, setLang, t } = useLanguage();
  const [companyName, setCompanyName] = useState('Customer Manager');
  const [logoPath, setLogoPath] = useState<string>();
  const [darkLogoPath, setDarkLogoPath] = useState<string>();
  const [isLightMode, setIsLightMode] = useState(() => localStorage.getItem('theme') === 'light');
  const [authReady, setAuthReady] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setAuthReady(true);
      return;
    }

    getCurrentUser()
      .then(({ data }) => {
        setCurrentUser(data);
        setIsAuthenticated(true);
      })
      .catch(() => {
        clearAuthToken();
        setCurrentUser(null);
        setIsAuthenticated(false);
      })
      .finally(() => {
        setAuthReady(true);
      });
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = isLightMode ? 'light' : 'dark';
    localStorage.setItem('theme', isLightMode ? 'light' : 'dark');
  }, [isLightMode]);

  useEffect(() => {
    if (!isAuthenticated) return;

    getCompanySettings().then(({ data }) => {
      setCompanyName(data.company_name || 'Customer Manager');
      setLogoPath(data.logo_path);
      setDarkLogoPath(data.dark_logo_path);
    }).catch(() => undefined);
  }, [isAuthenticated, location.pathname]);

  useEffect(() => {
    setIsMobileNavOpen(false);
  }, [location.pathname]);

  if (!authReady) {
    return (
      <main className="page-shell">
        <div className="card" style={{ maxWidth: 420, margin: '3rem auto' }}>
          <p className="page-copy">{t('Loading authentication...', 'Lade Authentifizierung...')}</p>
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <AuthPage onAuthenticated={(user) => {
      setCurrentUser(user);
      setIsAuthenticated(true);
    }} />;
  }

  const logout = async () => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        await logoutUser(refreshToken);
      } catch {
        // Ignore logout errors and clear local tokens anyway.
      }
    }
    clearAuthToken();
    setCurrentUser(null);
    setIsMobileNavOpen(false);
    setIsAuthenticated(false);
  };

  return (
    <div className={`app-root${isHome ? ' app-root--home' : ''}`}>
      <header className={`site-header${isHome ? ' site-header--over-hero' : ''}`}>
        <div className="container header-inner">
          <Link to="/" className="logo">
            {(isLightMode ? logoPath : darkLogoPath || logoPath) ? <img src={isLightMode ? logoPath : darkLogoPath || logoPath} alt={companyName} className="logo-image" /> : <span className="logo-name">{companyName}</span>}
          </Link>
          <button
            type="button"
            className={`nav-toggle${isMobileNavOpen ? ' is-open' : ''}`}
            aria-expanded={isMobileNavOpen}
            aria-controls="main-navigation"
            aria-label={isMobileNavOpen ? t('Close navigation', 'Navigation schließen') : t('Open navigation', 'Navigation öffnen')}
            onClick={() => setIsMobileNavOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
          <nav id="main-navigation" className={`main-nav${isMobileNavOpen ? ' is-open' : ''}`}>
            <NavLink to="/customers" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              {t('Customers', 'Kunden')}
            </NavLink>
            <NavLink to="/invoices" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              {t('Invoices', 'Rechnungen')}
            </NavLink>
            <NavLink to="/offers" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              {t('Offers', 'Angebote')}
            </NavLink>
            <NavLink to="/letters" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              {t('Letters', 'Briefe')}
            </NavLink>
            <NavLink to="/articles" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              {t('Articles', 'Artikel')}
            </NavLink>
            <NavLink to="/settings" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              {t('Settings', 'Einstellungen')}
            </NavLink>
            <button type="button" className="btn btn-secondary btn-small" onClick={logout}>
              {t('Logout', 'Abmelden')}
            </button>
            <div className="nav-controls">
              <button
                type="button"
                className="lang-toggle"
                aria-label="Toggle language"
                title={lang === 'en' ? 'Deutsch' : 'English'}
                onClick={() => setLang(lang === 'en' ? 'de' : 'en')}
              >
                {lang === 'en' ? 'DE' : 'EN'}
              </button>
              <button
                type="button"
                className="theme-toggle"
                aria-pressed={isLightMode}
                aria-label={isLightMode ? 'Switch to dark mode' : 'Switch to light mode'}
                title={isLightMode ? 'Switch to dark mode' : 'Switch to light mode'}
                onClick={() => setIsLightMode(!isLightMode)}
              >
                {isLightMode ? (
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4V2M12 22v-2M4 12H2M22 12h-2M6.34 6.34 4.93 4.93M19.07 19.07l-1.41-1.41M17.66 6.34l1.41-1.41M4.93 19.07l1.41-1.41M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z" /></svg>
                ) : (
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.4 15.3A8.5 8.5 0 0 1 8.7 3.6 8.5 8.5 0 1 0 20.4 15.3Z" /></svg>
                )}
              </button>
            </div>
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/customers" element={<CustomerList />} />
        <Route path="/customers/new" element={<CustomerForm />} />
        <Route path="/customers/:id/edit" element={<CustomerForm />} />
        <Route path="/invoices" element={<InvoiceList />} />
        <Route path="/invoices/new" element={<InvoiceForm />} />
        <Route path="/offers" element={<OfferList />} />
        <Route path="/offers/new" element={<OfferForm />} />
        <Route path="/letters" element={<LetterList />} />
        <Route path="/letters/new" element={<LetterForm />} />
        <Route path="/articles" element={<ArticleList />} />
        <Route path="/articles/new" element={<ArticleForm />} />
        <Route path="/articles/:id/edit" element={<ArticleForm />} />
        <Route path="/settings" element={<SettingsPage currentUser={currentUser} />} />
      </Routes>

      <footer className="site-footer">
        <div className="container footer-inner">
          <p className="footer-brandline">
            &copy; <span id="year">{new Date().getFullYear()}</span> made with{' '}
            <span className="footer-heart" aria-label="love" role="img">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 21.35 10.55 20.03C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3 9.24 3 10.91 3.81 12 5.09 13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35Z" />
              </svg>
            </span>{' '}
            by{' '}
            <a className="footer-brand-link" href="https://oxocode.com" target="_blank" rel="noreferrer">oXoCode</a>
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;
