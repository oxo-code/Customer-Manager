import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { getCustomers, createLetter, generateLetterDocument } from '../services/api';
import { Customer } from '../types/api';

const LetterForm: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | ''>('');
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await getCustomers();
      setCustomers(response.data);
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId) return;

    try {
      const response = await createLetter({
        customer_id: selectedCustomerId as number,
        subject,
        content,
        date,
      });
      await generateLetterDocument({
        letter_id: response.data.id,
      });
      navigate('/letters');
    } catch (error) {
      console.error('Error creating letter:', error);
    }
  };

  return (
    <main className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t('Letters', 'Briefe')}</p>
          <h1 className="page-title">{t('Create a new letter', 'Neuen Brief erstellen')}</h1>
          <p className="page-copy">{t('Create a new letter with subject and content.', 'Erstelle einen neuen Brief mit Betreff und Inhalt.')}</p>
        </div>
      </div>

      <div className="card">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>{t('Customer', 'Kunde')}</label>
            <select value={selectedCustomerId} onChange={(e) => setSelectedCustomerId(parseInt(e.target.value) || '')} required>
              <option value="">{t('Select customer', 'Kunde auswählen')}</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>{customer.name} {customer.firma && `(${customer.firma})`}</option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label>{t('Date', 'Datum')}</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </div>

          <div className="form-field">
            <label>{t('Subject', 'Betreff')}</label>
            <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)} required />
          </div>

          <div className="full-width">
            <p><label>{t('Content', 'Inhalt')}</label></p>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              placeholder={t('Enter the letter content...', 'Geben Sie den Briefinhalt ein...')}
              required
            />
          </div>

          <div className="full-width">
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">
                {t('Create letter', 'Brief erstellen')}
              </button>
              <button type="button" onClick={() => navigate('/letters')} className="btn btn-secondary">
                {t('Cancel', 'Abbrechen')}
              </button>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
};

export default LetterForm;