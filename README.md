# Customer Manager

A web application for managing customers and generating invoices.

## Setup

### Backend

1. Install Python 3.8+ from https://python.org
2. Install dependencies: `pip install -r backend/requirements.txt`
3. For PDF generation, install LibreOffice and ensure its program directory is in `PATH` (`libreoffice` on Linux; usually `soffice.exe` on Windows).
4. Run the backend: `python -m uvicorn backend.main:app --reload`

### Frontend

1. Install Node.js from https://nodejs.org
2. Install dependencies: `npm install`
3. Run the app in development mode: `npm run dev`
4. Run the app in production-style preview mode: `npm run prod`

## Usage

- Frontend dev server: http://127.0.0.1:5173
- Frontend production preview: http://127.0.0.1:4173
- Backend API: http://127.0.0.1:8001

## Features

- Customer management (CRUD)
- Invoice creation with automatic numbering
- Document generation from Word templates

## Template

Place your invoice_template.docx in `templates/docx/` with placeholders like {{customer_name}}, {{invoice_number}}, etc.