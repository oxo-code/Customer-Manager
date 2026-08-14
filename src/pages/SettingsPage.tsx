import React, { useEffect, useState } from 'react';
import { useLanguage } from '../i18n';
import { createManagedUser, deleteManagedUser, getCompanySettings, getManagedUsers, updateCompanySettings, updateManagedUserRole, uploadCompanyDarkLogo, uploadCompanyLogo, uploadDocumentLogo } from '../services/api';
import { AuthUser, CompanySettings } from '../types/api';

const emptySettings: Omit<CompanySettings, 'id' | 'logo_path' | 'dark_logo_path' | 'document_logo_path'> = {
  company_name: '', full_name: '', street: '', postal_code: '', city: '', country: '', email: '', phone: '',
  tax_number: '', vat_id: '', vat_rate: 19, bank_name: '', iban: '', bic: '',
};

const emptyNewUser = {
  username: '',
  password: '',
  role: 'user' as 'admin' | 'user',
};

interface SettingsPageProps {
  currentUser: AuthUser | null;
}

const SettingsPage: React.FC<SettingsPageProps> = ({ currentUser }) => {
  const [settings, setSettings] = useState(emptySettings);
  const [logoPath, setLogoPath] = useState<string>();
  const [darkLogoPath, setDarkLogoPath] = useState<string>();
  const [documentLogoPath, setDocumentLogoPath] = useState<string>();
  const [status, setStatus] = useState('');
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [userStatus, setUserStatus] = useState('');
  const [userLoading, setUserLoading] = useState(false);
  const [newUser, setNewUser] = useState(emptyNewUser);
  const { t } = useLanguage();

  const isAdmin = currentUser?.role === 'admin';

  useEffect(() => {
    getCompanySettings().then(({ data }) => {
      const { id, logo_path, dark_logo_path, document_logo_path, ...values } = data;
      setSettings(values);
      setLogoPath(logo_path);
      setDarkLogoPath(dark_logo_path);
      setDocumentLogoPath(document_logo_path);
    }).catch(() => setStatus(t('Settings could not be loaded.', 'Einstellungen konnten nicht geladen werden.')));
  }, [t]);

  useEffect(() => {
    if (!isAdmin) {
      setUsers([]);
      return;
    }

    setUserLoading(true);
    getManagedUsers()
      .then(({ data }) => {
        setUsers(data);
      })
      .catch((error) => {
        const backendMessage = error?.response?.data?.detail;
        setUserStatus(backendMessage || t('Users could not be loaded.', 'Benutzer konnten nicht geladen werden.'));
      })
      .finally(() => {
        setUserLoading(false);
      });
  }, [isAdmin, t]);

  const change = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    if (name === 'vat_rate') {
      if (value.trim() === '') {
        setSettings({ ...settings, vat_rate: 0 });
        return;
      }
      const normalized = Number.parseFloat(value.replace(',', '.'));
      setSettings({ ...settings, vat_rate: Number.isFinite(normalized) ? normalized : 0 });
      return;
    }
    setSettings({ ...settings, [name]: value });
  };

  const changeNewUser = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setNewUser({ ...newUser, [event.target.name]: event.target.value });
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
      if ((settings.vat_rate ?? 0) < 0 || (settings.vat_rate ?? 0) > 100) {
        setStatus(t('VAT rate must be between 0 and 100.', 'Der Steuersatz muss zwischen 0 und 100 liegen.'));
        return;
      }
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

  const createUser = async () => {
    setUserStatus('');

    try {
      if (!newUser.username.trim()) {
        throw new Error(t('Please enter a username.', 'Bitte Benutzername eingeben.'));
      }

      if (newUser.password.length < 8) {
        throw new Error(t('Password must have at least 8 characters.', 'Das Passwort muss mindestens 8 Zeichen haben.'));
      }

      const { data } = await createManagedUser({
        username: newUser.username.trim(),
        password: newUser.password,
        role: newUser.role,
      });
      setUsers((currentUsers) => [...currentUsers, data].sort((leftUser, rightUser) => leftUser.username.localeCompare(rightUser.username)));
      setNewUser(emptyNewUser);
      setUserStatus(t('User created.', 'Benutzer erstellt.'));
    } catch (error: any) {
      const backendMessage = error?.response?.data?.detail;
      setUserStatus(backendMessage || error?.message || t('The user could not be created.', 'Der Benutzer konnte nicht erstellt werden.'));
    }
  };

  const changeUserRole = async (userId: number, role: 'admin' | 'user') => {
    setUserStatus('');
    try {
      const { data } = await updateManagedUserRole(userId, { role });
      setUsers((currentUsers) => currentUsers.map((user) => (user.id === userId ? data : user)));
      setUserStatus(t('Permissions updated.', 'Rechte aktualisiert.'));
    } catch (error: any) {
      const backendMessage = error?.response?.data?.detail;
      setUserStatus(backendMessage || t('Permissions could not be updated.', 'Rechte konnten nicht aktualisiert werden.'));
    }
  };

  const removeUser = async (user: AuthUser) => {
    if (!window.confirm(t(`Delete user ${user.username}?`, `Benutzer ${user.username} löschen?`))) {
      return;
    }

    setUserStatus('');
    try {
      await deleteManagedUser(user.id);
      setUsers((currentUsers) => currentUsers.filter((entry) => entry.id !== user.id));
      setUserStatus(t('User deleted.', 'Benutzer gelöscht.'));
    } catch (error: any) {
      const backendMessage = error?.response?.data?.detail;
      setUserStatus(backendMessage || t('The user could not be deleted.', 'Der Benutzer konnte nicht gelöscht werden.'));
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
        <div className="form-field"><label>{t('VAT rate (%)', 'Steuersatz (%)')}</label><input type="number" min="0" max="100" step="0.01" name="vat_rate" value={settings.vat_rate ?? 19} onChange={change} /></div>
        <div className="form-field"><label>{t('Bank', 'Bank')}</label><input name="bank_name" value={settings.bank_name || ''} onChange={change} /></div><div className="form-field"><label>IBAN</label><input name="iban" value={settings.iban || ''} onChange={change} /></div><div className="form-field"><label>BIC</label><input name="bic" value={settings.bic || ''} onChange={change} /></div>
      </div></section>
      <section className="card settings-section">
        <div className="settings-section-head">
          <div>
            <h2>{t('User management', 'Benutzerverwaltung')}</h2>
            <p className="page-copy settings-section-copy">{t('Create additional admins or users and control their permissions.', 'Lege weitere Admins oder Benutzer an und steuere ihre Rechte.')}</p>
          </div>
          {currentUser && <span className={`role-pill role-pill--${currentUser.role}`}>{currentUser.role === 'admin' ? t('Admin', 'Admin') : t('User', 'Benutzer')}</span>}
        </div>

        {isAdmin ? (
          <>
            <div className="form-grid">
              <div className="form-field"><label>{t('Username', 'Benutzername')}</label><input name="username" value={newUser.username} onChange={changeNewUser} autoComplete="off" required /></div>
              <div className="form-field"><label>{t('Temporary password', 'Temporäres Passwort')}</label><input type="password" name="password" value={newUser.password} onChange={changeNewUser} autoComplete="new-password" required /></div>
              <div className="form-field"><label>{t('Role', 'Rolle')}</label><select name="role" value={newUser.role} onChange={changeNewUser}><option value="user">{t('User', 'Benutzer')}</option><option value="admin">{t('Admin', 'Admin')}</option></select></div>
              <div className="full-width action-row"><button className="btn btn-primary" type="button" onClick={createUser}>{t('Create user', 'Benutzer erstellen')}</button></div>
            </div>

            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('Username', 'Benutzername')}</th>
                    <th>{t('Role', 'Rolle')}</th>
                    <th>{t('Permissions', 'Rechte')}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => {
                    const isCurrentUser = currentUser?.id === user.id;
                    return (
                      <tr key={user.id}>
                        <td>
                          <div className="user-cell">
                            <span>{user.username}</span>
                            {isCurrentUser && <span className="user-meta">{t('You', 'Du')}</span>}
                          </div>
                        </td>
                        <td><span className={`role-pill role-pill--${user.role}`}>{user.role === 'admin' ? t('Admin', 'Admin') : t('User', 'Benutzer')}</span></td>
                        <td>
                          <div className="button-group user-actions">
                            <select value={user.role} onChange={(event) => changeUserRole(user.id, event.target.value as 'admin' | 'user')} aria-label={t(`Role for ${user.username}`, `Rolle für ${user.username}`)}>
                              <option value="user">{t('User', 'Benutzer')}</option>
                              <option value="admin">{t('Admin', 'Admin')}</option>
                            </select>
                            <button type="button" className="btn btn-secondary btn-small" onClick={() => removeUser(user)} disabled={isCurrentUser}>{t('Delete', 'Löschen')}</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {!userLoading && users.length === 0 && (
                    <tr>
                      <td colSpan={3}>{t('No additional users yet.', 'Noch keine weiteren Benutzer vorhanden.')}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="form-status" role="status">{t('Only admins can create users or change permissions.', 'Nur Admins können Benutzer anlegen oder Rechte ändern.')}</p>
        )}
      </section>
      <div className="action-row"><button className="btn btn-primary" type="submit">{t('Save settings', 'Einstellungen speichern')}</button>{status && <p className="form-status" role="status">{status}</p>}</div>
      {userStatus && <p className="form-status" role="status">{userStatus}</p>}
    </form>
  </main>;
};

export default SettingsPage;