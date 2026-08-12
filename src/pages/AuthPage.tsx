import React, { useEffect, useState } from 'react';
import { useLanguage } from '../i18n';
import { getAuthBootstrap, loginUser, registerFirstUser, setAuthToken, setRefreshToken } from '../services/api';

interface AuthPageProps {
  onAuthenticated: () => void;
}

const AuthPage: React.FC<AuthPageProps> = ({ onAuthenticated }) => {
  const [setupRequired, setSetupRequired] = useState<boolean | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { t } = useLanguage();

  useEffect(() => {
    getAuthBootstrap()
      .then(({ data }) => {
        setSetupRequired(data.setup_required);
      })
      .catch(() => {
        setError(t('Authentication bootstrap failed.', 'Authentifizierungs-Initialisierung fehlgeschlagen.'));
      });
  }, [t]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (!username.trim()) {
        throw new Error(t('Please enter a username.', 'Bitte Benutzername eingeben.'));
      }

      if (password.length < 8) {
        throw new Error(t('Password must have at least 8 characters.', 'Das Passwort muss mindestens 8 Zeichen haben.'));
      }

      if (setupRequired && password !== confirmPassword) {
        throw new Error(t('Passwords do not match.', 'Passwörter stimmen nicht überein.'));
      }

      const request = setupRequired
        ? registerFirstUser({ username: username.trim(), password })
        : loginUser({ username: username.trim(), password });

      const { data } = await request;
      setAuthToken(data.access_token);
      setRefreshToken(data.refresh_token);
      onAuthenticated();
    } catch (err: any) {
      const backendMessage = err?.response?.data?.detail;
      setError(backendMessage || err?.message || t('Authentication failed.', 'Authentifizierung fehlgeschlagen.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <div className="card" style={{ maxWidth: 480, margin: '3rem auto' }}>
        <p className="eyebrow">{t('Security', 'Sicherheit')}</p>
        <h1 className="page-title" style={{ marginTop: 0 }}>
          {setupRequired ? t('Create the first admin account', 'Erstes Admin-Konto erstellen') : t('Sign in', 'Anmelden')}
        </h1>
        <p className="page-copy">
          {setupRequired
            ? t('This is the first start. Create your initial login now.', 'Dies ist der erste Start. Erstelle jetzt den initialen Login.')
            : t('Sign in to access customer management.', 'Melde dich an, um das Kundenmanagement zu nutzen.')}
        </p>

        <form onSubmit={submit} className="form-grid" style={{ marginTop: '1rem' }}>
          <div className="form-field full-width">
            <label>{t('Username', 'Benutzername')}</label>
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
          </div>

          <div className="form-field full-width">
            <label>{t('Password', 'Passwort')}</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={setupRequired ? 'new-password' : 'current-password'}
              required
            />
          </div>

          {setupRequired && (
            <div className="form-field full-width">
              <label>{t('Confirm password', 'Passwort bestätigen')}</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
          )}

          {error && (
            <p className="form-status full-width" role="alert" style={{ color: '#ff8d8d' }}>
              {error}
            </p>
          )}

          <div className="full-width action-row">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? t('Please wait...', 'Bitte warten...') : setupRequired ? t('Create account', 'Konto erstellen') : t('Sign in', 'Anmelden')}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};

export default AuthPage;
