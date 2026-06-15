FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend context into a /app/backend directory
# This allows `uvicorn backend.main:app` to resolve properly from /app
COPY . ./backend/

# Shell form CMD so $PORT expands at runtime
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
