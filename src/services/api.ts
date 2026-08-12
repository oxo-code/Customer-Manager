import axios from 'axios';
import { Article, CompanySettings, Customer, Invoice, InvoiceItem, Letter, Offer, OfferItem } from '../types/api';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const api = axios.create({
  baseURL: apiBaseUrl,
});

export const getCustomers = () => api.get<Customer[]>('/customers');
export const getCustomer = (id: number) => api.get<Customer>(`/customers/${id}`);
export const createCustomer = (customer: Omit<Customer, 'id' | 'created_at'>) => api.post<Customer>('/customers', customer);
export const updateCustomer = (id: number, customer: Omit<Customer, 'id' | 'created_at'>) => api.put<Customer>(`/customers/${id}`, customer);
export const deleteCustomer = (id: number) => api.delete(`/customers/${id}`);

export const getInvoices = () => api.get<Invoice[]>('/invoices');
export const getInvoice = (id: number) => api.get<Invoice>(`/invoices/${id}`);
export const createInvoice = (data: { customer_id: number; date: string; items: InvoiceItem[] }) => api.post<Invoice>('/invoices/create', data);
export const updateInvoiceStatus = (id: number, status: 'draft' | 'final') => api.patch<Invoice>(`/invoices/${id}/status`, { status });
export const deleteInvoice = (id: number) => api.delete(`/invoices/${id}`);

export const generateDocument = (data: { invoice_id: number }) => api.post('/documents/generate', data);

export const getOffers = () => api.get<Offer[]>('/offers');
export const getOffer = (id: number) => api.get<Offer>(`/offers/${id}`);
export const createOffer = (data: { customer_id: number; date: string; items: OfferItem[] }) => api.post<Offer>('/offers/create', data);
export const updateOfferStatus = (id: number, status: 'draft' | 'final') => api.patch<Offer>(`/offers/${id}/status`, { status });
export const deleteOffer = (id: number) => api.delete(`/offers/${id}`);

export const generateOfferDocument = (data: { offer_id: number }) => api.post('/documents/generate-offer', data);

export const getLetters = () => api.get<Letter[]>('/letters');
export const getLetter = (id: number) => api.get<Letter>(`/letters/${id}`);
export const createLetter = (data: { customer_id: number; subject: string; content: string; date: string }) => api.post<Letter>('/letters/create', data);

export const generateLetterDocument = (data: { letter_id: number }) => api.post('/documents/generate-letter', data);

export const getArticles = () => api.get<Article[]>('/articles');
export const getArticle = (id: number) => api.get<Article>(`/articles/${id}`);
export const createArticle = (data: Omit<Article, 'id' | 'created_at'>) => api.post<Article>('/articles', data);
export const updateArticle = (id: number, data: Omit<Article, 'id' | 'created_at'>) => api.put<Article>(`/articles/${id}`, data);
export const deleteArticle = (id: number) => api.delete(`/articles/${id}`);

export const getCompanySettings = () => api.get<CompanySettings>('/settings');
export const updateCompanySettings = (settings: Omit<CompanySettings, 'id' | 'logo_path' | 'dark_logo_path' | 'document_logo_path'>) => api.put<CompanySettings>('/settings', settings);
const uploadLogo = (file: File, path: string) => {
  const data = new FormData();
  data.append('file', file);
  return api.post<CompanySettings>(path, data);
};
export const uploadCompanyLogo = (file: File) => uploadLogo(file, '/settings/logo');
export const uploadCompanyDarkLogo = (file: File) => uploadLogo(file, '/settings/dark-logo');
export const uploadDocumentLogo = (file: File) => uploadLogo(file, '/settings/document-logo');