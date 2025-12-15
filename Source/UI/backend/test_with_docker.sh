#!/bin/bash

# Quick test using Docker to verify Pydantic typing implementation

set -e

echo "🔍 Quick Pydantic Integration Test via Docker"
echo "============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Build minimal test image
echo "Building test image..."
docker build -t flood-backend-test -f - . << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install minimal dependencies
RUN pip install pydantic==2.5.3 pandas==2.1.4 sqlalchemy==2.0.25

# Copy only essential files
COPY app/schemas.py /app/app/
COPY app/db_models.py /app/app/
COPY tests/test_integration_simple.py /app/tests/

# Create necessary directories
RUN mkdir -p /app/app

# Create __init__.py files to make directories Python packages
RUN touch /app/app/__init__.py

# Run the test
CMD python /app/tests/test_integration_simple.py
EOF

if [ $? -ne 0 ]; then
    print_error "Failed to build test image"
    exit 1
fi

print_status "Test image built successfully"

# Run the test
echo "Running integration test..."
docker run --rm flood-backend-test

if [ $? -eq 0 ]; then
    print_status "Integration test passed! 🎉"
    echo ""
    echo "✅ Pydantic typing implementation verified successfully!"
else
    print_error "Integration test failed! ❌"
    exit 1
fi

# Clean up
docker rmi flood-backend-test >/dev/null 2>&1 || true