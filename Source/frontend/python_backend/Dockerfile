FROM python:3.11

WORKDIR /srv

# Install system dependencies for psycopg2 and PostGIS
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache layering
COPY requirements.txt .

# Install Python dependencies (includes test dependencies)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files including tests
COPY . .

EXPOSE 18080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:18080/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18080"]
