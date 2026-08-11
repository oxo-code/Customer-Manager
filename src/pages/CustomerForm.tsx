import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getCustomer, createCustomer, updateCustomer } from '../services/api';
import { Customer } from '../types/api';

const CustomerForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState<Omit<Customer, 'id' | 'created_at'>>({
    name: '',
    firma: '',
    adresse: '',
    plz: '',
    ort: '',
    email: '',
    telefon: '',
  });

  useEffect(() => {
    if (id && id !== 'new') {
      loadCustomer(parseInt(id));
    }
  }, [id]);

  const loadCustomer = async (customerId: number) => {
    try {
      const response = await getCustomer(customerId);
      setCustomer(response.data);
    } catch (error) {
      console.error('Error loading customer:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (id === 'new') {
        await createCustomer(customer);
      } else if (id) {
        await updateCustomer(parseInt(id), customer);
      }
      navigate('/customers');
    } catch (error) {
      console.error('Error saving customer:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setCustomer({ ...customer, [e.target.name]: e.target.value });
  };

  return (
    <main className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Kunden</p>
          <h1 className="page-title">{id === 'new' ? 'Neuen Kunden anlegen' : 'Kunden bearbeiten'}</h1>
          <p className="page-copy">Pflege hier die Kundendaten für Rechnungen, Angebote und Dokumente.</p>
        </div>
        <Link to="/customers" className="btn btn-secondary">
          Zur Kundenliste
        </Link>
      </div>

      <div className="card">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Name</label>
            <input type="text" name="name" value={customer.name} onChange={handleChange} required />
          </div>
          <div className="form-field">
            <label>Firma</label>
            <input type="text" name="firma" value={customer.firma || ''} onChange={handleChange} />
          </div>
          <div className="form-field full-width">
            <label>Adresse</label>
            <textarea name="adresse" value={customer.adresse} onChange={handleChange} required />
          </div>
          <div className="form-field">
            <label>PLZ</label>
            <input type="text" name="plz" value={customer.plz} onChange={handleChange} required />
          </div>
          <div className="form-field">
            <label>Ort</label>
            <input type="text" name="ort" value={customer.ort} onChange={handleChange} required />
          </div>
          <div className="form-field">
            <label>Email</label>
            <input type="email" name="email" value={customer.email || ''} onChange={handleChange} />
          </div>
          <div className="form-field">
            <label>Telefon</label>
            <input type="tel" name="telefon" value={customer.telefon || ''} onChange={handleChange} />
          </div>
          <div className="full-width action-row">
            <button type="submit" className="btn btn-primary">
              Speichern
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/customers')}>
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};

export default CustomerForm;