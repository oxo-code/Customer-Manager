import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { createCustomer, getCustomer, updateCustomer } from '../services/api';

type CustomerFormState = {
	name: string;
	firma: string;
	adresse: string;
	plz: string;
	ort: string;
	email: string;
	telefon: string;
};

const emptyForm: CustomerFormState = {
	name: '',
	firma: '',
	adresse: '',
	plz: '',
	ort: '',
	email: '',
	telefon: '',
};

const CustomerForm: React.FC = () => {
	const navigate = useNavigate();
	const { id } = useParams();
	const { t } = useLanguage();
	const [form, setForm] = useState<CustomerFormState>(emptyForm);

	useEffect(() => {
		if (!id) return;

		getCustomer(Number(id))
			.then(({ data }) => {
				setForm({
					name: data.name || '',
					firma: data.firma || '',
					adresse: data.adresse || '',
					plz: data.plz || '',
					ort: data.ort || '',
					email: data.email || '',
					telefon: data.telefon || '',
				});
			})
			.catch((error) => {
				console.error('Error loading customer details:', error);
			});
	}, [id]);

	const handleChange = (field: keyof CustomerFormState, value: string) => {
		setForm((current) => ({ ...current, [field]: value }));
	};

	const handleSubmit = async (event: React.FormEvent) => {
		event.preventDefault();

		if (!form.name.trim() || !form.adresse.trim() || !form.plz.trim() || !form.ort.trim()) {
			alert(t('Name, address, postal code and city are required.', 'Name, Adresse, PLZ und Ort sind erforderlich.'));
			return;
		}

		const payload = {
			name: form.name.trim(),
			firma: form.firma.trim(),
			adresse: form.adresse.trim(),
			plz: form.plz.trim(),
			ort: form.ort.trim(),
			email: form.email.trim(),
			telefon: form.telefon.trim(),
		};

		try {
			if (id) {
				await updateCustomer(Number(id), payload);
			} else {
				await createCustomer(payload);
			}

			navigate('/customers');
		} catch (error) {
			console.error('Error saving customer:', error);
			alert(t('The customer could not be saved.', 'Der Kunde konnte nicht gespeichert werden.'));
		}
	};

	return (
		<main className="page-shell">
			<div className="page-header">
				<div>
					<p className="eyebrow">{t('Customers', 'Kunden')}</p>
					<h1 className="page-title">{id ? t('Edit customer', 'Kunde bearbeiten') : t('New customer', 'Neuer Kunde')}</h1>
					<p className="page-copy">{t('Keep the customer details up to date for all documents and records.', 'Pflege die Kundendaten für alle Dokumente und Einträge aktuell.')}</p>
				</div>
			</div>

			<div className="card">
				<form className="form-layout" onSubmit={handleSubmit}>
					<div className="form-field">
						<label>{t('Name', 'Name')}</label>
						<input value={form.name} onChange={(event) => handleChange('name', event.target.value)} required />
					</div>

					<div className="form-field">
						<label>{t('Company', 'Firma')}</label>
						<input value={form.firma} onChange={(event) => handleChange('firma', event.target.value)} />
					</div>

					<div className="form-field full-width">
						<label>{t('Street and house number', 'Straße und Hausnummer')}</label>
						<input value={form.adresse} onChange={(event) => handleChange('adresse', event.target.value)} required />
					</div>

					<div className="form-field">
						<label>{t('Postal code', 'PLZ')}</label>
						<input value={form.plz} onChange={(event) => handleChange('plz', event.target.value)} required />
					</div>

					<div className="form-field">
						<label>{t('City', 'Ort')}</label>
						<input value={form.ort} onChange={(event) => handleChange('ort', event.target.value)} required />
					</div>

					<div className="form-field">
						<label>{t('Email', 'E-Mail')}</label>
						<input type="email" value={form.email} onChange={(event) => handleChange('email', event.target.value)} />
					</div>

					<div className="form-field">
						<label>{t('Phone', 'Telefon')}</label>
						<input value={form.telefon} onChange={(event) => handleChange('telefon', event.target.value)} />
					</div>

					<div className="full-width action-row">
						<button type="submit" className="btn btn-primary">
							{id ? t('Save', 'Speichern') : t('Create customer', 'Kunde anlegen')}
						</button>
						<button type="button" className="btn btn-secondary" onClick={() => navigate('/customers')}>
							{t('Cancel', 'Abbrechen')}
						</button>
					</div>
				</form>
			</div>
		</main>
	);
};

export default CustomerForm;
