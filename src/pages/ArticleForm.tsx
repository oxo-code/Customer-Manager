import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createArticle, getArticle, updateArticle } from '../services/api';

const ArticleForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [defaultQuantity, setDefaultQuantity] = useState('1');
  const [defaultPrice, setDefaultPrice] = useState('');

  useEffect(() => {
    if (isEdit) {
      loadArticle();
    }
  }, [id]);

  const loadArticle = async () => {
    try {
      const response = await getArticle(Number(id));
      const a = response.data;
      setName(a.name);
      setDescription(a.description || '');
      setDefaultQuantity(String(a.default_quantity));
      setDefaultPrice(String(a.default_price));
    } catch (error) {
      console.error('Error loading article:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      name,
      description: description || undefined,
      default_quantity: parseFloat(defaultQuantity.replace(',', '.')) || 1,
      default_price: parseFloat(defaultPrice.replace(',', '.')) || 0,
    };
    try {
      if (isEdit) {
        await updateArticle(Number(id), data);
      } else {
        await createArticle(data);
      }
      navigate('/articles');
    } catch (error) {
      console.error('Error saving article:', error);
    }
  };

  return (
    <main className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Artikel</p>
          <h1 className="page-title">{isEdit ? 'Artikel bearbeiten' : 'Neuer Artikel'}</h1>
          <p className="page-copy">Lege einen Artikel mit Standardmenge und Standardpreis an.</p>
        </div>
      </div>

      <div className="card">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Artikelname"
              required
            />
          </div>

          <div className="form-field">
            <label>Beschreibung</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optionale Beschreibung"
            />
          </div>

          <div className="form-field">
            <label>Standardmenge</label>
            <input
              type="text"
              value={defaultQuantity}
              onChange={(e) => setDefaultQuantity(e.target.value)}
              placeholder="Menge (z. B. 1 oder 2,5)"
              inputMode="decimal"
            />
          </div>

          <div className="form-field">
            <label>Standardpreis (€)</label>
            <input
              type="text"
              value={defaultPrice}
              onChange={(e) => setDefaultPrice(e.target.value)}
              placeholder="Preis (z. B. 10,99)"
              inputMode="decimal"
            />
          </div>

          <div className="full-width action-row">
            <button type="submit" className="btn btn-primary">
              {isEdit ? 'Speichern' : 'Artikel anlegen'}
            </button>
            <button type="button" onClick={() => navigate('/articles')} className="btn btn-secondary">
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};

export default ArticleForm;
