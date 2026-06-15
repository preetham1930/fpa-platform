# FP&A Platform

This repository contains the local vertical slice for the FP&A Platform (Phase 1).

## Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js & npm (for frontend)

## Running Locally

### 1. Database
Start the Postgres container:
```bash
docker-compose up -d
```

### 2. Backend
Create a virtual environment and install dependencies:
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

pip install -r backend/requirements.txt
```

Run tests to verify the core variance service:
```bash
set PYTHONPATH=.
pytest backend/tests/test_variance.py
```

Seed the database with sample data:
```bash
set PYTHONPATH=.
python backend/seed.py
```

Start the FastAPI server:
```bash
set PYTHONPATH=.
uvicorn backend.main:app --reload
```
The API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend (Coming soon)
Once the frontend is built, you will navigate to the `frontend` folder and run `npm install` and `npm run dev`.
