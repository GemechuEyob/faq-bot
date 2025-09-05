FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    fonts-unifont \
    fonts-liberation \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright without browsers first
# RUN pip install playwright

# Install Playwright dependencies and browser
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/scripts/entrypoint.sh

ENTRYPOINT ["sh", "/app/scripts/entrypoint.sh"]