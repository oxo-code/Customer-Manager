# Customer Manager

A web application for managing customers and generating invoices.

## Setup

### Backend

1. Install Python 3.8+ from https://python.org
2. Install dependencies: `pip install -r backend/requirements.txt`
3. For PDF generation, install Microsoft Word (docx2pdf uses Word on Windows).
4. Generate a local SSL certificate: `py backend/generate_ssl.py --host localhost --host 127.0.0.1`
5. Run the backend publicly on all interfaces with HTTPS: `py -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --ssl-keyfile backend/.local/key.pem --ssl-certfile backend/.local/cert.pem`

### Frontend

1. Install Node.js from https://nodejs.org
2. Install dependencies: `npm install`
3. Build the production frontend bundle: `npm run build`
4. Run the app in development mode: `npm run dev`
5. Run the app in production-style preview mode: `npm run prod`
6. The Vite dev and preview servers are configured with `host: '0.0.0.0'` so they can be reached from outside localhost.

## Production

- Run the frontend build first: `npm run build`
- The backend serves the built frontend from the `dist` folder on port `8001`.
- If you want to open the backend via a public IP or hostname over HTTPS, generate the certificate with every target host/IP included, for example: `py backend/generate_ssl.py --host localhost --host 127.0.0.1 --host <server-ip>`
- In production, open the app via `https://<server-ip>:8001` instead of Vite's preview port when the certificate includes that IP or hostname.
- The backend keeps the API routes under `/api` and serves the frontend at the root URL.

## Usage

- Frontend dev server: http://127.0.0.1:5173
- Frontend production preview: http://127.0.0.1:4173
- Backend API / served frontend: https://127.0.0.1:8001
- Public network access: https://<server-ip>:8001

## Authentication

- On first app start, create the initial admin account in the login screen.
- Session uses access + refresh tokens.
- If `AUTH_SECRET_KEY` is not set, the backend creates a local secret file in `backend/.local/` that is gitignored.
- The local SQLite database now lives in `backend/.local/` by default and is gitignored.
- Reset a password locally with one command:
	- `npm run reset-password -- --username <username> --password <new-password>`

## Git Safety

- The repository ignores local databases, uploads, and generated auth secrets.
- A local pre-commit hook in `.githooks/pre-commit` blocks staging `.env` files and local runtime data.
- Activate it once on your machine with: `git config core.hooksPath .githooks`

## Features

- Customer management (CRUD)
- Invoice creation with automatic numbering
- Document generation from Word templates

## Template

Place your invoice_template.docx in `templates/docx/` with placeholders like {{customer_name}}, {{invoice_number}}, etc.
