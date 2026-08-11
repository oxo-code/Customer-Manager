import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getArticles, deleteArticle } from '../services/api';
import { Article } from '../types/api';

const ArticleList: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);

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
    if (!confirm('Artikel wirklich löschen?')) return;
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
          <p className="eyebrow">Artikel</p>
          <h1 className="page-title">Artikelstamm</h1>
          <p className="page-copy">Verwalte deine Artikel mit Standardmenge und Standardpreis.</p>
        </div>
        <Link to="/articles/new" className="btn btn-primary">
          Neuer Artikel
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Beschreibung</th>
                <th>Standardmenge</th>
                <th>Standardpreis</th>
                <th>Aktionen</th>
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
                      Bearbeiten
                    </Link>
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => handleDelete(article.id)}
                    >
                      Löschen
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
