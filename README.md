# Customer Manager

A web application for managing customers and generating invoices.

## Setup

### Backend

1. Install Python 3.8+ from https://python.org
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Run the backend: `uvicorn backend.main:app --reload`

### Frontend

1. Install Node.js from https://nodejs.org
2. Install dependencies: `npm install`
3. Run the frontend: `npm run dev`

## Usage

- Access the app at http://localhost:5173
- Backend API at http://localhost:8000

## Features

- Customer management (CRUD)
- Invoice creation with automatic numbering
- Document generation from Word templates

## Template

Place your invoice_template.docx in `templates/docx/` with placeholders like {{customer_name}}, {{invoice_number}}, etc.