import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { deleteCustomer, getCustomers } from '../services/api';
import { Customer } from '../types/api';

const CustomerList: React.FC = () => {
	const [customers, setCustomers] = useState<Customer[]>([]);
	const { t } = useLanguage();

	const loadCustomers = async () => {
		try {
			const response = await getCustomers();
			setCustomers(response.data.sort((a, b) => b.id - a.id));
		} catch (error) {
			console.error('Error loading customers:', error);
		}
	};

	useEffect(() => {
		loadCustomers();
	}, []);

	const handleDelete = async (id: number) => {
		if (!confirm(t('Delete this customer?', 'Diesen Kunden wirklich löschen?'))) return;

		try {
			await deleteCustomer(id);
			setCustomers((current) => current.filter((customer) => customer.id !== id));
		} catch (error) {
			console.error('Error deleting customer:', error);
			alert(t('The customer could not be deleted.', 'Der Kunde konnte nicht gelöscht werden.'));
		}
	};

	return (
		<main className="page-shell">
			<div className="page-header">
				<div>
					<p className="eyebrow">{t('Customers', 'Kunden')}</p>
					<h1 className="page-title">{t('Customer overview', 'Kundenübersicht')}</h1>
					<p className="page-copy">{t('Manage your customers and keep all contact details in one place.', 'Verwalte deine Kunden und behalte alle Kontaktdaten an einem Ort.')}</p>
				</div>
				<Link to="/customers/new" className="btn btn-primary">
					{t('New customer', 'Neuer Kunde')}
				</Link>
			</div>

			<div className="card">
				<div className="table-wrap">
					<table className="data-table">
						<thead>
							<tr>
								<th>{t('Name', 'Name')}</th>
								<th>{t('Company', 'Firma')}</th>
								<th>{t('Email', 'E-Mail')}</th>
								<th>{t('Phone', 'Telefon')}</th>
								<th>{t('Actions', 'Aktionen')}</th>
							</tr>
						</thead>
						<tbody>
							{customers.map((customer) => (
								<tr key={customer.id}>
									<td>{customer.name}</td>
									<td>{customer.firma || '—'}</td>
									<td>{customer.email || '—'}</td>
									<td>{customer.telefon || '—'}</td>
									<td className="button-group">
										<Link to={`/customers/${customer.id}/edit`} className="btn btn-secondary btn-small">
											{t('Edit', 'Bearbeiten')}
										</Link>
										<button
											type="button"
											className="btn btn-secondary btn-small"
											onClick={() => handleDelete(customer.id)}
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

export default CustomerList;
