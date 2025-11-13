#!/bin/sh

# Health check script for Flood Prediction API
# Tests both the API server and database connectivity

# Check if the API server is responding
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "API health check passed"
    exit 0
else
    echo "API health check failed"
    exit 1
fi