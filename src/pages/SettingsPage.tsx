import React, { useEffect, useState } from 'react';
import { useLanguage } from '../i18n';
import { getCompanySettings, updateCompanySettings, uploadCompanyDarkLogo, uploadCompanyLogo, uploadDocumentLogo } from '../services/api';
import { CompanySettings } from '../types/api';

const emptySettings: Omit<CompanySettings, 'id' | 'logo_path' | 'dark_logo_path' | 'document_logo_path'> = {
  company_name: '', full_name: '', street: '', postal_code: '', city: '', country: '', email: '', phone: '',
  tax_number: '', vat_id: '', bank_name: '', iban: '', bic: '',
};

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState(emptySettings);
  const [logoPath, setLogoPath] = useState<string>();
  const [darkLogoPath, setDarkLogoPath] = useState<string>();
  const [documentLogoPath, setDocumentLogoPath] = useState<string>();
  const [status, setStatus] = useState('');
  const { t } = useLanguage();

  useEffect(() => {
    getCompanySettings().then(({ data }) => {
      const { id, logo_path, dark_logo_path, document_logo_path, ...values } = data;
      setSettings(values);
      setLogoPath(logo_path);
      setDarkLogoPath(dark_logo_path);
      setDocumentLogoPath(document_logo_path);
    }).catch(() => setStatus(t('Settings could not be loaded.', 'Einstellungen konnten nicht geladen werden.')));
  }, [t]);

  const change = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSettings({ ...settings, [event.target.name]: event.target.value });
  };

  const selectDarkLogo = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const { data } = await uploadCompanyDarkLogo(file);
      setDarkLogoPath(data.dark_logo_path);
      setStatus(t('Dark mode logo uploaded.', 'Dark-Mode-Logo hochgeladen.'));
    } catch {
      setStatus(t('The dark mode logo could not be uploaded.', 'Das Dark-Mode-Logo konnte nicht hochgeladen werden.'));
    }
  };

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await updateCompanySettings(settings);
      setStatus(t('Settings saved.', 'Einstellungen gespeichert.'));
    } catch {
      setStatus(t('Settings could not be saved.', 'Einstellungen konnten nicht gespeichert werden.'));
    }
  };

  const selectLogo = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const { data } = await uploadCompanyLogo(file);
      setLogoPath(data.logo_path);
      setStatus(t('Logo uploaded.', 'Logo hochgeladen.'));
    } catch {
      setStatus(t('The logo could not be uploaded.', 'Das Logo konnte nicht hochgeladen werden.'));
    }
  };

  const selectDocumentLogo = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const { data } = await uploadDocumentLogo(file);
      setDocumentLogoPath(data.document_logo_path);
      setStatus(t('Document logo uploaded.', 'Dokumentenlogo hochgeladen.'));
    } catch {
      setStatus(t('The document logo could not be uploaded.', 'Das Dokumentenlogo konnte nicht hochgeladen werden.'));
    }
  };

  return <main className="page-shell">
    <div className="page-header"><div><p className="eyebrow">{t('Settings', 'Einstellungen')}</p><h1 className="page-title">{t('Company details', 'Unternehmensdaten')}</h1><p className="page-copy">{t('These details are used centrally for management and document templates.', 'Diese Angaben stehen zentral für deine Verwaltung und Dokumentvorlagen bereit.')}</p></div></div>
    <form className="settings-form" onSubmit={save}>
      <section className="card settings-section">
        <h2>{t('Display', 'Darstellung')}</h2>
        <div className="logo-upload">
          {logoPath ? <img src={logoPath} alt={t('Current company logo', 'Aktuelles Firmenlogo')} className="company-logo-preview" /> : <div className="company-logo-placeholder">{t('No logo', 'Kein Logo')}</div>}
          <div className="form-field"><label htmlFor="company-logo">{t('Company logo', 'Firmenlogo')}</label><input id="company-logo" type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" onChange={selectLogo} /><small>PNG, JPG, WebP or SVG</small></div>
        </div>
        <div className="logo-upload dark-logo-upload">
          {darkLogoPath ? <img src={darkLogoPath} alt={t('Dark mode company logo', 'Dark-Mode-Firmenlogo')} className="company-logo-preview company-logo-preview--dark" /> : <div className="company-logo-placeholder company-logo-placeholder--dark">{t('No dark mode logo', 'Kein Dark-Mode-Logo')}</div>}
          <div className="form-field"><label htmlFor="company-dark-logo">{t('Logo for dark mode', 'Logo für schwarzen Modus')}</label><input id="company-dark-logo" type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" onChange={selectDarkLogo} /><small>{t('Use a light logo for dark backgrounds.', 'Nutze ein helles Logo für dunkle Hintergründe.')}</small></div>
        </div>
        <div className="logo-upload">
          {documentLogoPath ? <img src={documentLogoPath} alt={t('Current document logo', 'Aktuelles Dokumentenlogo')} className="company-logo-preview" /> : <div className="company-logo-placeholder">{t('No document logo', 'Kein Dokumentenlogo')}</div>}
          <div className="form-field"><label htmlFor="document-logo">{t('Document logo', 'Dokumentenlogo')}</label><input id="document-logo" type="file" accept="image/png,image/jpeg" onChange={selectDocumentLogo} /><small>PNG or JPG</small></div>
        </div>
        <div className="form-grid">
          <div className="form-field full-width"><label>{t('Company name', 'Firmenname')}</label><input name="company_name" value={settings.company_name} onChange={change} required /></div>
          <div className="form-field full-width"><label>{t('Sign-off name', 'Name für Grußformel')}</label><input name="full_name" value={settings.full_name || ''} onChange={change} placeholder={t('e.g. Max Mustermann', 'z. B. Max Mustermann')} /></div>
        </div>
      </section>
      <section className="card settings-section"><h2>{t('Contact and address', 'Kontakt und Anschrift')}</h2><div className="form-grid">
        <div className="form-field full-width"><label>{t('Street and house number', 'Straße und Hausnummer')}</label><input name="street" value={settings.street || ''} onChange={change} /></div>
        <div className="form-field"><label>{t('Postal code', 'PLZ')}</label><input name="postal_code" value={settings.postal_code || ''} onChange={change} /></div><div className="form-field"><label>{t('City', 'Ort')}</label><input name="city" value={settings.city || ''} onChange={change} /></div>
        <div className="form-field"><label>{t('Country', 'Land')}</label><input name="country" value={settings.country || ''} onChange={change} /></div><div className="form-field"><label>{t('Email', 'E-Mail')}</label><input type="email" name="email" value={settings.email || ''} onChange={change} /></div><div className="form-field"><label>{t('Phone', 'Telefon')}</label><input name="phone" value={settings.phone || ''} onChange={change} /></div>
      </div></section>
      <section className="card settings-section"><h2>{t('Tax and bank', 'Steuer und Bank')}</h2><div className="form-grid">
        <div className="form-field"><label>{t('Tax number', 'Steuernummer')}</label><input name="tax_number" value={settings.tax_number || ''} onChange={change} /></div><div className="form-field"><label>{t('VAT ID', 'USt-IdNr.')}</label><input name="vat_id" value={settings.vat_id || ''} onChange={change} /></div>
        <div className="form-field"><label>{t('Bank', 'Bank')}</label><input name="bank_name" value={settings.bank_name || ''} onChange={change} /></div><div className="form-field"><label>IBAN</label><input name="iban" value={settings.iban || ''} onChange={change} /></div><div className="form-field"><label>BIC</label><input name="bic" value={settings.bic || ''} onChange={change} /></div>
      </div></section>
      <div className="action-row"><button className="btn btn-primary" type="submit">{t('Save settings', 'Einstellungen speichern')}</button>{status && <p className="form-status" role="status">{status}</p>}</div>
    </form>
  </main>;
};

export default SettingsPage;