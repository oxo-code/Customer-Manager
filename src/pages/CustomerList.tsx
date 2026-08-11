import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCustomers, deleteCustomer } from '../services/api';
import { Customer } from '../types/api';

const CustomerList: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await getCustomers();
      setCustomers(response.data.sort((a, b) => b.id - a.id));
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this customer?')) {
      try {
        await deleteCustomer(id);
        loadCustomers();
      } catch (error) {
        console.error('Error deleting customer:', error);
      }
    }
  };

  return (
    <main className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Customers</p>
          <h1 className="page-title">Kundenverwaltung</h1>
          <p className="page-copy">Alle Kunden im Blick behalten. Hier kannst du neue Kunden anlegen und bestehende Daten bearbeiten.</p>
        </div>
        <Link to="/customers/new" className="btn btn-primary">
          Neuer Kunde
        </Link>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Firma</th>
                <th>Ort</th>
                <th>Email</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {customers.map(customer => (
                <tr key={customer.id}>
                  <td>{customer.name}</td>
                  <td>{customer.firma}</td>
                  <td>{customer.ort}</td>
                  <td>{customer.email}</td>
                  <td>
                    <Link to={`/customers/${customer.id}/edit`} className="btn btn-secondary">
                      Edit
                    </Link>
                    <button type="button" className="btn btn-secondary" onClick={() => handleDelete(customer.id)}>
                      Delete
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

export default CustomerList;