#!/bin/sh

echo "Waiting for database..."
echo "Trying to connect with:"
echo "Host: $POSTGRES_HOST"
echo "User: $POSTGRES_USER"
echo "Database: $POSTGRES_DB"

until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1
do
  echo "Database is still starting... Connection error:"
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;"
  sleep 2
done

echo "Database is ready!"

# Initialize database schema
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOSQL'
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS scraped_data (
    id SERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    content TEXT,
    embedding vector(384),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON scraped_data USING ivfflat (embedding vector_cosine_ops);
EOSQL

echo "Database schema initialized!"

# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload