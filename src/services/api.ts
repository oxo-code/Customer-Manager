import axios from 'axios';
import { Article, AuthBootstrap, AuthTokenResponse, AuthUser, CompanySettings, Customer, Invoice, InvoiceItem, Letter, Offer, OfferItem } from '../types/api';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const api = axios.create({
  baseURL: apiBaseUrl,
});

const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
let refreshInFlight: Promise<string | null> | null = null;

export const getAuthToken = () => localStorage.getItem(AUTH_TOKEN_KEY);

export const setAuthToken = (token: string) => {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
};

export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setRefreshToken = (token: string) => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
};

export const clearAuthToken = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config as any;
    const status = error?.response?.status;
    const isAuthRoute = originalRequest?.url?.includes('/auth/login') || originalRequest?.url?.includes('/auth/register-first') || originalRequest?.url?.includes('/auth/refresh');

    if (status !== 401 || !originalRequest || originalRequest._retry || isAuthRoute) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (!refreshInFlight) {
      refreshInFlight = (async () => {
        const refreshToken = getRefreshToken();
        if (!refreshToken) return null;

        try {
          const { data } = await api.post<AuthTokenResponse>('/auth/refresh', { refresh_token: refreshToken });
          setAuthToken(data.access_token);
          setRefreshToken(data.refresh_token);
          return data.access_token;
        } catch {
          clearAuthToken();
          return null;
        } finally {
          refreshInFlight = null;
        }
      })();
    }

    const newAccessToken = await refreshInFlight;
    if (!newAccessToken) {
      return Promise.reject(error);
    }

    originalRequest.headers = originalRequest.headers || {};
    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
    return api(originalRequest);
  }
);

export const getAuthBootstrap = () => api.get<AuthBootstrap>('/auth/bootstrap');
export const registerFirstUser = (data: { username: string; password: string }) => api.post<AuthTokenResponse>('/auth/register-first', data);
export const loginUser = (data: { username: string; password: string }) => api.post<AuthTokenResponse>('/auth/login', data);
export const refreshAuth = (refreshToken: string) => api.post<AuthTokenResponse>('/auth/refresh', { refresh_token: refreshToken });
export const logoutUser = (refreshToken: string) => api.post('/auth/logout', { refresh_token: refreshToken });
export const getCurrentUser = () => api.get<AuthUser>('/auth/me');

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