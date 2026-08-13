import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { getCustomers, createInvoice, generateDocument, getArticles } from '../services/api';
import { Customer, InvoiceItem, Article } from '../types/api';

const InvoiceForm: React.FC = () => {
  const navigate = useNavigate();
  const { t, lang } = useLanguage();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | ''>('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [items, setItems] = useState<Array<InvoiceItem & { quantity_str?: string; unit_price_str?: string }>>([
    { description: '', quantity: 0, unit_price: 0, quantity_str: '', unit_price_str: '' }
  ]);

  useEffect(() => {
    loadCustomers();
    loadArticles();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await getCustomers();
      setCustomers(response.data);
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const loadArticles = async () => {
    try {
      const response = await getArticles();
      setArticles(response.data);
    } catch (error) {
      console.error('Error loading articles:', error);
    }
  };

  const handleSelectArticle = (index: number, articleId: string) => {
    const article = articles.find(a => a.id === parseInt(articleId));
    if (!article) return;
    const newItems = [...items];
    newItems[index] = {
      ...newItems[index],
      description: article.name + (article.description ? ` – ${article.description}` : ''),
      quantity: article.default_quantity,
      unit_price: article.default_price,
      quantity_str: String(article.default_quantity),
      unit_price_str: String(article.default_price),
    };
    setItems(newItems);
  };

  const handleAddItem = () => {
    setItems([...items, { description: '', quantity: 0, unit_price: 0, quantity_str: '', unit_price_str: '' }]);
  };

  const handleItemChange = (index: number, field: keyof InvoiceItem, value: string | number) => {
    const newItems = [...items];
    if (field === 'quantity' || field === 'unit_price') {
      // Für String-Felder: speichere den eingegebenen Wert als String (auch leere Strings)
      const strField = field + '_str' as 'quantity_str' | 'unit_price_str';
      const stringValue = value as string;
      newItems[index] = { ...newItems[index], [strField]: stringValue };

      // Konvertiere zu Number nur wenn nicht leer
      if (stringValue.trim() === '') {
        newItems[index] = { ...newItems[index], [field]: 0 };
      } else {
        const cleanValue = stringValue.replace(',', '.').replace(/[^0-9.]/g, '');
        const numValue = parseFloat(cleanValue) || 0;
        newItems[index] = { ...newItems[index], [field]: numValue };
      }
    } else {
      newItems[index] = { ...newItems[index], [field]: value };
    }
    setItems(newItems);
  };

  const handleNumericInput = (index: number, field: 'quantity' | 'unit_price', value: string) => {
    // Erlaube freie Eingabe auch mit leeren Werten
    handleItemChange(index, field, value);
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId) return;

    // Validiere dass alle Items korrekte Werte haben
    for (const item of items) {
      if (!item.description.trim()) {
        alert(t('Every item needs a description.', 'Alle Artikel brauchen eine Beschreibung.'));
        return;
      }
      if (item.quantity <= 0) {
        alert(t('Quantity must be greater than 0.', 'Menge muss größer als 0 sein.'));
        return;
      }
      if (item.unit_price <= 0) {
        alert(t('Price must be greater than 0.', 'Preis muss größer als 0 sein.'));
        return;
      }
    }

    try {
      // Bereinige items für API: entferne String-Felder
      const cleanItems = items.map(item => ({
        description: item.description,
        quantity: item.quantity,
        unit_price: item.unit_price
      }));

      const response = await createInvoice({
        customer_id: selectedCustomerId as number,
        date,
        items: cleanItems,
      });
      await generateDocument({
        invoice_id: response.data.id,
      }, lang);
      navigate('/invoices');
    } catch (error) {
      console.error('Error creating invoice:', error);
    }
  };

  return (
    <main className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t('Invoices', 'Rechnungen')}</p>
          <h1 className="page-title">{t('Create a new invoice', 'Neue Rechnung erstellen')}</h1>
          <p className="page-copy">{t('Create a new invoice and add item positions directly.', 'Erstelle eine neue Rechnung und füge Artikelpositionen direkt hinzu.')}</p>
        </div>
      </div>

      <div className="card">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>{t('Customer', 'Kunde')}</label>
            <select value={selectedCustomerId} onChange={(e) => setSelectedCustomerId(parseInt(e.target.value) || '')} required>
              <option value="">{t('Select customer...', 'Kunden auswählen ...')}</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>{customer.name}</option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label>{t('Date', 'Datum')}</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </div>

          <div className="full-width">
            <h2>{t('Items', 'Positionen')}</h2>
            <div className="item-list">
              {items.map((item, index) => (
                <div key={index} className="item-row form-field full-width">
                  <select onChange={(e) => handleSelectArticle(index, e.target.value)} defaultValue="">
                    <option value="">{t('Select article...', 'Artikel auswählen ...')}</option>
                    {articles.map(a => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                  <input
                    type="text"
                    placeholder={t('Item description', 'Artikelbeschreibung')}
                    value={item.description}
                    onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                    required
                  />
                  <input
                    type="text"
                    placeholder={t('Quantity (e.g. 2 or 2.5)', 'Menge (z. B. 2 oder 2,5)')}
                    value={item.quantity_str ?? ''}
                    onChange={(e) => handleNumericInput(index, 'quantity', e.target.value)}
                    inputMode="decimal"
                  />
                  <input
                    type="text"
                    placeholder={t('Unit price (e.g. 10.99)', 'Einzelpreis (z. B. 10,99)')}
                    value={item.unit_price_str ?? ''}
                    onChange={(e) => handleNumericInput(index, 'unit_price', e.target.value)}
                    inputMode="decimal"
                  />
                  <button type="button" className="btn btn-secondary" onClick={() => handleRemoveItem(index)}>
                    {t('Remove', 'Entfernen')}
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="full-width action-row">
            <button type="button" className="btn btn-secondary" onClick={handleAddItem}>
              {t('Add item', 'Position hinzufügen')}
            </button>
            <button type="submit" className="btn btn-primary">
              {t('Create invoice', 'Rechnung erstellen')}
            </button>
            <button type="button" onClick={() => navigate('/invoices')} className="btn btn-secondary">
              {t('Cancel', 'Abbrechen')}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};

export default InvoiceForm;