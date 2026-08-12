import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { createArticle, getArticle, updateArticle } from '../services/api';

const ArticleForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;
  const { t } = useLanguage();

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
          <p className="eyebrow">{t('Articles', 'Artikel')}</p>
          <h1 className="page-title">{isEdit ? t('Edit article', 'Artikel bearbeiten') : t('New article', 'Neuer Artikel')}</h1>
          <p className="page-copy">{t('Create an article with default quantity and default price.', 'Lege einen Artikel mit Standardmenge und Standardpreis an.')}</p>
        </div>
      </div>

      <div className="card">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>{t('Name', 'Name')}</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('Article name', 'Artikelname')}
              required
            />
          </div>

          <div className="form-field">
            <label>{t('Description', 'Beschreibung')}</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('Optional description', 'Optionale Beschreibung')}
            />
          </div>

          <div className="form-field">
            <label>{t('Default quantity', 'Standardmenge')}</label>
            <input
              type="text"
              value={defaultQuantity}
              onChange={(e) => setDefaultQuantity(e.target.value)}
              placeholder={t('Quantity (e.g. 1 or 2.5)', 'Menge (z. B. 1 oder 2,5)')}
              inputMode="decimal"
            />
          </div>

          <div className="form-field">
            <label>{t('Default price (€)', 'Standardpreis (€)')}</label>
            <input
              type="text"
              value={defaultPrice}
              onChange={(e) => setDefaultPrice(e.target.value)}
              placeholder={t('Price (e.g. 10.99)', 'Preis (z. B. 10,99)')}
              inputMode="decimal"
            />
          </div>

          <div className="full-width action-row">
            <button type="submit" className="btn btn-primary">
              {isEdit ? t('Save', 'Speichern') : t('Create article', 'Artikel anlegen')}
            </button>
            <button type="button" onClick={() => navigate('/articles')} className="btn btn-secondary">
              {t('Cancel', 'Abbrechen')}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};

export default ArticleForm;
