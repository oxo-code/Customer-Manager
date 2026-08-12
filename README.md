# Customer Manager

A web application for managing customers and generating invoices.

## Setup

### Backend

1. Install Python 3.8+ from https://python.org
2. Install dependencies: `pip install -r backend/requirements.txt`
3. For PDF generation, install Microsoft Word (docx2pdf uses Word on Windows).
4. Optional: set `AUTH_SECRET_KEY` and `CUSTOMER_MANAGER_DB_PATH` if you want custom local paths.
5. Run the backend: `python -m uvicorn backend.main:app --reload`

### Frontend

1. Install Node.js from https://nodejs.org
2. Install dependencies: `npm install`
3. Run the app in development mode: `npm run dev`
4. Run the app in production-style preview mode: `npm run prod`

## Usage

- Frontend dev server: http://127.0.0.1:5173
- Frontend production preview: http://127.0.0.1:4173
- Backend API: http://127.0.0.1:8001

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