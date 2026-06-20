FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if necessary (e.g. for Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize db directory/files if needed
RUN mkdir -p static/uploads static/generated

ENV PORT=8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
