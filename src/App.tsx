import React from 'react';
import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
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

const App: React.FC = () => {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div className={`app-root${isHome ? ' app-root--home' : ''}`}>
      <header className={`site-header${isHome ? ' site-header--over-hero' : ''}`}>
        <div className="container header-inner">
          <a href="/" className="logo">
            <img src="/logo.png" alt="Customer Manager" className="logo-image" />
            <span className="logo-text">Customer Manager</span>
          </a>
          <nav className="main-nav">
            <NavLink to="/customers" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              Kunden
            </NavLink>
            <NavLink to="/invoices" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              Rechnungen
            </NavLink>
            <NavLink to="/offers" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              Angebote
            </NavLink>
            <NavLink to="/letters" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              Briefe
            </NavLink>
            <NavLink to="/articles" className={({ isActive }) => (isActive ? 'is-active' : undefined)}>
              Artikel
            </NavLink>
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
      </Routes>

      <footer className="site-footer">
        <div className="container footer-inner">
          <p>
            &copy; <span id="year">{new Date().getFullYear()}</span> Customer Manager. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;
