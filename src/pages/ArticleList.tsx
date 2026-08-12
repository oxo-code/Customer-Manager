import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { getArticles, deleteArticle } from '../services/api';
import { Article } from '../types/api';

const ArticleList: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const { t } = useLanguage();

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    try {
      const response = await getArticles();
      setArticles(response.data.sort((a, b) => b.id - a.id));
    } catch (error) {
      console.error('Error loading articles:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm(t('Delete this article?', 'Artikel wirklich löschen?'))) return;
    try {
      await deleteArticle(id);
      setArticles(articles.filter(a => a.id !== id));
    } catch (error) {
      console.error('Error deleting article:', error);
    }
  };

  return (
    <main className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t('Articles', 'Artikel')}</p>
          <h1 className="page-title">{t('Article master data', 'Artikelstamm')}</h1>
          <p className="page-copy">{t('Manage articles with default quantity and default price.', 'Verwalte deine Artikel mit Standardmenge und Standardpreis.')}</p>
        </div>
        <Link to="/articles/new" className="btn btn-primary">
          {t('New article', 'Neuer Artikel')}
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('Name', 'Name')}</th>
                <th>{t('Description', 'Beschreibung')}</th>
                <th>{t('Default quantity', 'Standardmenge')}</th>
                <th>{t('Default price', 'Standardpreis')}</th>
                <th>{t('Actions', 'Aktionen')}</th>
              </tr>
            </thead>
            <tbody>
              {articles.map(article => (
                <tr key={article.id}>
                  <td>{article.name}</td>
                  <td>{article.description || '—'}</td>
                  <td>{article.default_quantity}</td>
                  <td>{article.default_price.toFixed(2)} €</td>
                  <td className="button-group">
                    <Link to={`/articles/${article.id}/edit`} className="btn btn-secondary btn-small">
                      {t('Edit', 'Bearbeiten')}
                    </Link>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => handleDelete(article.id)}
                    >
                      {t('Delete', 'Löschen')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
};

export default ArticleList;
