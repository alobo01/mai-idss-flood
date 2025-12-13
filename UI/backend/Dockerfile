FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
# Copy requirements first for better caching
COPY UI/backend/requirements.txt .

# Install Python dependencies
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip --disable-pip-version-check install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY UI/backend/app/ ./app/
COPY UI/backend/run.py .
COPY UI/scripts/ /app/scripts/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/Programs
ENV SCRIPTS_DIR=/app/scripts

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "run.py"]
