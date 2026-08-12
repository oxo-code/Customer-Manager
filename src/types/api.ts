export interface Customer {
  id: number;
  name: string;
  firma?: string;
  adresse: string;
  plz: string;
  ort: string;
  email?: string;
  telefon?: string;
  created_at: string;
}

export interface InvoiceItem {
  id?: number;
  description: string;
  quantity: number;
  unit_price: number;
  total_price?: number;
}

export interface Invoice {
  id: number;
  customer_id: number;
  invoice_number: string;
  date: string;
  total_amount: number;
  status: string;
  created_at: string;
  customer: Customer;
  items: InvoiceItem[];
}

export interface OfferItem {
  id?: number;
  description: string;
  quantity: number;
  unit_price: number;
  total_price?: number;
}

export interface Offer {
  id: number;
  customer_id: number;
  offer_number: string;
  date: string;
  total_amount: number;
  status: string;
  created_at: string;
  customer: Customer;
  items: OfferItem[];
}

export interface Letter {
  id: number;
  customer_id: number;
  subject: string;
  content: string;
  date: string;
  created_at: string;
  customer: Customer;
}

export interface Article {
  id: number;
  name: string;
  description?: string;
  default_quantity: number;
  default_price: number;
  created_at: string;
}

export interface CompanySettings {
  id: number;
  company_name: string;
  full_name?: string;
  street?: string;
  postal_code?: string;
  city?: string;
  country?: string;
  email?: string;
  phone?: string;
  tax_number?: string;
  vat_id?: string;
  bank_name?: string;
  iban?: string;
  bic?: string;
  logo_path?: string;
  dark_logo_path?: string;
  document_logo_path?: string;
}

export interface AuthBootstrap {
  setup_required: boolean;
}

export interface AuthUser {
  id: number;
  username: string;
  role: 'admin' | 'user';
}

export interface AuthCreateUserRequest {
  username: string;
  password: string;
  role: 'admin' | 'user';
}

export interface AuthUpdateUserRoleRequest {
  role: 'admin' | 'user';
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  user: AuthUser;
}