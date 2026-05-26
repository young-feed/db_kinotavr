FROM python:3.11-slim
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
CMD while ! pg_isready -h $DB_HOST -p 5432 -U $DB_USER; do sleep 1; done; uvicorn main:app --host 0.0.0.0 --port 8000