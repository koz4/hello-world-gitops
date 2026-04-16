FROM python:3.11-slim

WORKDIR /app

# Instalacja zależności systemowych dla psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port domyślny dla aplikacji
EXPOSE 8080

# Uruchomienie aplikacji na porcie 8080 (standard OpenShift)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
