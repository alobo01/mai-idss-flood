#!/bin/bash

# Test script for flood prediction backend
# Uses Docker to run tests with proper isolation and dependencies

set -e

echo "🌊 Flood Prediction Backend - Test Runner"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

print_status "docker-compose is available"

# Create test reports directory
mkdir -p test-reports
print_status "Created test-reports directory"

# Stop any existing test containers
echo "Cleaning up any existing test containers..."
docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true

# Build and run tests
echo "Building test environment..."
docker-compose -f docker-compose.test.yml build test-runner

if [ $? -ne 0 ]; then
    print_error "Failed to build test environment"
    exit 1
fi

print_status "Test environment built successfully"

echo "Running tests..."
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit test-runner

TEST_EXIT_CODE=$?

# Bring down containers
docker-compose -f docker-compose.test.yml down -v

# Check test results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_status "All tests passed! 🎉"

    # Check if coverage reports were generated
    if [ -f "test-reports/coverage.xml" ]; then
        print_status "Coverage report generated: test-reports/coverage.xml"
    fi

    if [ -f "test-reports/junit.xml" ]; then
        print_status "JUnit report generated: test-reports/junit.xml"
    fi

    if [ -d "htmlcov" ]; then
        print_status "HTML coverage report generated: htmlcov/index.html"
    fi

    # Show coverage summary if available
    if [ -f "htmlcov/index.html" ]; then
        echo ""
        echo "Coverage Summary:"
        echo "================"
        # Extract coverage percentage from HTML report
        COVERAGE_PERCENT=$(grep -o 'class="pc_cov">[0-9]*%' htmlcov/index.html | sed 's/class="pc_cov">//; s/%//')
        if [ ! -z "$COVERAGE_PERCENT" ]; then
            if [ $COVERAGE_PERCENT -ge 80 ]; then
                print_status "Coverage: ${COVERAGE_PERCENT}% (✓)"
            elif [ $COVERAGE_PERCENT -ge 60 ]; then
                print_warning "Coverage: ${COVERAGE_PERCENT}% (acceptable)"
            else
                print_error "Coverage: ${COVERAGE_PERCENT}% (needs improvement)"
            fi
        fi
    fi

else
    print_error "Tests failed! ❌"

    # Show error details if available
    if [ -f "test-reports/junit.xml" ]; then
        echo ""
        echo "Test Failures:"
        echo "==============="
        # Parse JUnit XML for failures
        python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('test-reports/junit.xml')
    root = tree.getroot()
    for testcase in root.findall('.//failure'):
        test_name = testcase.get('classname') + '.' + testcase.get('name')
        message = testcase.get('message', 'No message')
        print(f'❌ {test_name}')
        print(f'   {message}')
except Exception as e:
    print(f'Could not parse test results: {e}')
"
    fi

    exit 1
fi

echo ""
echo "📊 Test Summary:"
echo "==============="