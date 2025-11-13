# API Testing Guide

Comprehensive guide for testing the Flood Prediction API endpoints, including automated testing strategies and manual testing procedures.

## 🧪 Testing Overview

### Testing Environment
- **Base URL**: `http://localhost:8080`
- **Documentation**: `http://localhost:8080/api-docs/`
- **Database**: PostgreSQL with test data populated

### Testing Strategies
1. **Manual Testing** - Interactive testing via Swagger UI
2. **Automated Testing** - Scripted tests with various tools
3. **Integration Testing** - Testing with real applications
4. **Load Testing** - Performance and scalability testing

## 🔧 Manual Testing

### Using Swagger UI

The interactive Swagger UI at `http://localhost:8080/api-docs/` provides the easiest way to test the API:

1. **Open Documentation**: Navigate to `http://localhost:8080/api-docs/`
2. **Select Endpoint**: Click on any endpoint to expand it
3. **Try It Out**: Click the "Try it out" button
4. **Execute**: Click "Execute" to send a real request
5. **Review Response**: View the actual database response

### curl Testing Examples

Basic curl commands for testing API endpoints:

#### Health Check
```bash
curl -v http://localhost:8080/health
```

#### Get All Zones
```bash
curl -v http://localhost:8080/api/zones
```

#### Filtered Requests
```bash
# Get high severity alerts
curl -v "http://localhost:8080/api/alerts?severity=high"

# Get available resources
curl -v "http://localhost:8080/api/resources?status=available"

# Get risk assessments for 24h horizon
curl -v "http://localhost:8080/api/risk?timeHorizon=24h"
```

#### POST Requests
```bash
# Send communication
curl -X POST http://localhost:8080/api/comms \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms",
    "from": "Emergency Command",
    "to": "Zone Residents",
    "message": "Test evacuation message",
    "priority": "high"
  }'

# Acknowledge alert
curl -X POST http://localhost:8080/api/alerts/30000000-0000-0000-0000-000000000001/ack \
  -H "Content-Type: application/json" \
  -d '{"acknowledgedBy":"John Doe"}'
```

### Browser Testing

Use browser developer tools for testing:

```javascript
// Test GET request
fetch('http://localhost:8080/api/zones')
  .then(response => response.json())
  .then(data => console.log(data));

// Test POST request
fetch('http://localhost:8080/api/comms', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    channel: 'email',
    from: 'test@example.com',
    to: 'recipient@example.com',
    message: 'Test message',
    priority: 'normal'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🤖 Automated Testing

### Node.js Testing

Install required packages:
```bash
npm install axios mocha chai
```

#### Test Suite Example
```javascript
// test/api.test.js
const axios = require('axios');
const { expect } = require('chai');

const API_BASE = 'http://localhost:8080';

describe('Flood Prediction API Tests', () => {

  describe('Health Check', () => {
    it('should return healthy status', async () => {
      const response = await axios.get(`${API_BASE}/health`);
      expect(response.status).to.equal(200);
      expect(response.data.status).to.equal('ok');
      expect(response.data.database).to.equal('connected');
    });
  });

  describe('Zones API', () => {
    it('should return zones as GeoJSON', async () => {
      const response = await axios.get(`${API_BASE}/api/zones`);
      expect(response.status).to.equal(200);
      expect(response.data.type).to.equal('FeatureCollection');
      expect(response.data.features).to.be.an('array');
      expect(response.data.features[0].type).to.equal('Feature');
    });

    it('should return valid zone properties', async () => {
      const response = await axios.get(`${API_BASE}/api/zones`);
      const feature = response.data.features[0];

      expect(feature.properties).to.have.property('id');
      expect(feature.properties).to.have.property('name');
      expect(feature.properties).to.have.property('population');
      expect(feature.properties).to.have.property('area_km2');
    });
  });

  describe('Alerts API', () => {
    it('should return alerts array', async () => {
      const response = await axios.get(`${API_BASE}/api/alerts`);
      expect(response.status).to.equal(200);
      expect(response.data).to.be.an('array');
    });

    it('should filter alerts by severity', async () => {
      const response = await axios.get(`${API_BASE}/api/alerts?severity=high`);
      expect(response.status).to.equal(200);

      response.data.forEach(alert => {
        expect(alert.severity).to.equal('high');
      });
    });

    it('should filter alerts by acknowledgment status', async () => {
      const response = await axios.get(`${API_BASE}/api/alerts?acknowledged=false`);
      expect(response.status).equal(200);

      response.data.forEach(alert => {
        expect(alert.acknowledged).to.be.false;
      });
    });
  });

  describe('Risk Assessment API', () => {
    it('should return risk assessments', async () => {
      const response = await axios.get(`${API_BASE}/api/risk`);
      expect(response.status).to.equal(200);
      expect(typeof response.data).to.equal('object');
    });

    it('should filter by time horizon', async () => {
      const response = await axios.get(`${API_BASE}/api/risk?timeHorizon=24h`);
      expect(response.status).to.equal(200);

      // Each risk assessment should have the correct time horizon
      Object.values(response.data).forEach(risk => {
        expect(risk.timeHorizon).to.equal('24h');
      });
    });
  });

  describe('Resources API', () => {
    it('should return resources array', async () => {
      const response = await axios.get(`${API_BASE}/api/resources`);
      expect(response.status).to.equal(200);
      expect(response.data).to.be.an('array');
    });

    it('should filter resources by status', async () => {
      const response = await axios.get(`${API_BASE}/api/resources?status=available`);
      expect(response.status).to.equal(200);

      response.data.forEach(resource => {
        expect(resource.status).to.equal('available');
      });
    });
  });

  describe('Communications API', () => {
    it('should create communication', async () => {
      const communicationData = {
        channel: 'sms',
        from: 'Emergency Command Center',
        to: 'Test Recipient',
        message: 'Test message',
        priority: 'normal'
      };

      const response = await axios.post(`${API_BASE}/api/comms`, communicationData);
      expect(response.status).to.equal(201);
      expect(response.data.success).to.be.true;
      expect(response.data.communication).to.have.property('id');
      expect(response.data.communication.message).to.equal('Test message');
    });

    it('should retrieve communications', async () => {
      const response = await axios.get(`${API_BASE}/api/comms`);
      expect(response.status).to.equal(200);
      expect(response.data).to.be.an('array');
    });
  });

  describe('Alert Acknowledgment', () => {
    let alertId;

    before(async () => {
      // Get an alert to acknowledge
      const alertsResponse = await axios.get(`${API_BASE}/api/alerts?limit=1`);
      if (alertsResponse.data.length > 0) {
        alertId = alertsResponse.data[0].id;
      }
    });

    it('should acknowledge alert', async () => {
      if (!alertId) {
        this.skip(); // Skip if no alerts available
      }

      const ackData = { acknowledgedBy: 'Test User' };
      const response = await axios.post(`${API_BASE}/api/alerts/${alertId}/ack`, ackData);
      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true);
      expect(response.data.alert.acknowledged).to.be.true;
      expect(response.data.alert.acknowledgedBy).to.equal('Test User');
    });
  });

  describe('Error Handling', () => {
    it('should return 404 for non-existent endpoint', async () => {
      try {
        await axios.get(`${API_BASE}/api/nonexistent`);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(404);
      }
    });

    it('should return 400 for invalid alert ID', async () => {
      try {
        await axios.post(`${API_BASE}/api/alerts/invalid-id/ack`, {});
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(404);
      }
    });
  });

  describe('Data Validation', () => {
    it('should validate communication required fields', async () => {
      const invalidData = {
        channel: 'sms',
        // Missing required fields: from, to, message
      };

      try {
        await axios.post(`${API_BASE}/api/comms`, invalidData);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(400);
      }
    });

    it('should validate alert acknowledgment data', async () => {
      try {
        await axios.post(`${API_BASE}/api/alerts/test-id/ack`, {});
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(404);
      }
    });
  });
});
```

Run the tests:
```bash
# Install dependencies
npm install axios mocha chai --save-dev

# Run tests
npx mocha test/api.test.js

# Run with verbose output
npx mocha test/api.test.js --reporter spec
```

### Python Testing

Install required packages:
```bash
pip install requests pytest
```

#### Test Suite Example
```python
# test_api.py
import requests
import pytest
import json

API_BASE = "http://localhost:8080"

class TestFloodPredictionAPI:

    def test_health_check(self):
        """Test API health check endpoint"""
        response = requests.get(f"{API_BASE}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"

    def test_get_zones(self):
        """Test zones endpoint"""
        response = requests.get(f"{API_BASE}/api/zones")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) > 0

        # Check first feature structure
        feature = data["features"][0]
        assert feature["type"] == "Feature"
        assert "properties" in feature
        assert "geometry" in feature

    def test_get_alerts(self):
        """Test alerts endpoint"""
        response = requests.get(f"{API_BASE}/api/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_alerts_filtering(self):
        """Test alert filtering by severity"""
        response = requests.get(f"{API_BASE}/api/alerts?severity=high")
        assert response.status_code == 200
        data = response.json()
        assert all(alert["severity"] == "high" for alert in data)

    def test_send_communication(self):
        """Test sending communication"""
        comm_data = {
            "channel": "sms",
            "from": "Test Sender",
            "to": "Test Recipient",
            "message": "Test message",
            "priority": "normal"
        }

        response = requests.post(f"{API_BASE}/api/comms", json=comm_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "communication" in data
        assert data["communication"]["message"] == "Test message"

    def test_acknowledge_alert(self):
        """Test alert acknowledgment"""
        # First get an alert
        alerts_response = requests.get(f"{API_BASE}/api/alerts?limit=1")
        if alerts_response.status_code == 200 and alerts_response.json():
            alert = alerts_response.json()[0]
            alert_id = alert["id"]

            # Acknowledge the alert
            ack_data = {"acknowledgedBy": "Test User"}
            response = requests.post(f"{API_BASE}/api/alerts/{alert_id}/ack", json=ack_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["alert"]["acknowledged"] is True

    def test_not_found(self):
        """Test 404 error handling"""
        response = requests.get(f"{API_BASE}/api/nonexistent")
        assert response.status_code == 404

    def test_get_risk_assessments(self):
        """Test risk assessments endpoint"""
        response = requests.get(f"{API_BASE}/api/risk")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

if __name__ == "__main__":
    pytest.main([__file__])
```

Run the tests:
```bash
# Run all tests
python -m pytest test_api.py -v

# Run with coverage
pip install pytest-cov
python -m pytest test_api.py --cov=report
```

## 🔍 Integration Testing

### React Component Testing

Test React components with real API data:

```javascript
// src/hooks/__tests__/useApi.test.js
import { renderHook, act } from '@testing-library/react-hooks';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useZones, useAlerts, useResources } from '../useApi';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
      },
    },
  });
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('API Hooks', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = createWrapper();
  });

  test('useZones fetches zone data', async () => {
    const { result } = renderHook(() => useZones(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isSuccess).toBe(true);
    expect(result.current.data).toBeDefined();
    expect(Array.isArray(result.current.data)).toBe(true);
  });

  test('useAlerts fetches alert data', async () => {
    const { result } = renderHook(() => useAlerts(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isSuccess).toBe(true);
    expect(result.current.data).toBeDefined();
    expect(Array.isArray(result.current.data)).toBe(true);
  });

  test('useResources fetches resource data', async () => {
    const { result } = renderHook(() => useResources(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isSuccess).toBe(true);
    expect(result.current.data).toBeDefined();
    expect(Array.isArray(result.current.data)).toBe(true);
  });
});
```

### End-to-End Testing

Test complete user flows with Playwright:

```javascript
// tests/e2e/api-integration.spec.js
import { test, expect } from '@playwright/test';

test.describe('API Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost');

    // Wait for API to be available
    const response = await page.request.get('http://localhost:8080/health');
    expect(response.status()).toBe(200);
  });

  test('should load and display zone data on map', async ({ page }) => {
    // Navigate to planner map
    await page.click('[data-testid="planner-map-link"]');

    // Wait for map to load
    await page.waitForSelector('[data-testid="leaflet-map"]');

    // Check if zones are loaded (by checking if map features exist)
    const zonesResponse = await page.request.get('http://localhost:8080/api/zones');
    expect(zonesResponse.status()).toBe(200);

    const zonesData = zonesResponse.json();
    expect(zonesData.type).toBe('FeatureCollection');
    expect(zonesData.features.length).toBeGreaterThan(0);
  });

  test('should display and manage alerts', async ({ page }) => {
    // Navigate to alerts
    await page.click('[data-testid="alerts-link"]');

    // Check if alerts are loaded
    const alertsResponse = await page.request.get('http://localhost:8080/api/alerts');
    expect(alertsResponse.status()).toBe(200);

    // Test alert acknowledgment
    if (alertsResponse.status() === 200 && alertsResponse.json().length > 0) {
      const alert = alertsResponse.json()[0];

      // Find acknowledge button for first alert
      const ackButton = page.locator(`[data-testid="ack-alert-${alert.id}"]`);

      if (await ackButton.count() > 0) {
        await ackButton.click();

        // Verify acknowledgment in UI
        const updatedAlertsResponse = await page.request.get(`http://localhost:8080/api/alerts/${alert.id}`);
        const updatedAlert = updatedAlertsResponse.json();
        expect(updatedAlert.acknowledged).toBe(true);
      }
    }
  });

  test('should test communication sending', async ({ page }) => {
    // Navigate to communications
    await page.click('[data-testid="communications-link"]');

    // Find send communication form
    const sendButton = page.locator('[data-testid="send-communication"]');

    if (await sendButton.count() > 0) {
      await sendButton.click();

      // Verify communication was created via API
      const commsResponse = await page.request.get('http://localhost:8080/api/comms');
      expect(commsResponse.status()).toBe(200);
      expect(commsResponse.json()).toBeInstanceOf(Array);
    }
  });
});
```

Run E2E tests:
```bash
npx playwright test e2e/api-integration.spec.js
```

## 📊 Load Testing

### k6 Load Testing

Create a load testing script:

```javascript
// load-test.js
import http from 'k6/http';
import { check } from 'k6';

const API_BASE = 'http://localhost:8080';

export let options = {
  stages: [
    { duration: '30s', target: 10, rps: 10 },
    { duration: '1m', target: 50, rps: 50 },
    { duration: '30s', target: 100, rps: 100 },
  ],
};

export default function () {
  // Health check
  check(API_BASE + '/health');

  // Test zones endpoint
  group('Zones API', () => {
    let response = http.get(`${API_BASE}/api/zones`);
    check(response.status, 200);

    // Test with parameters
    response = http.get(`${API_BASE}/api/zones`, {
      headers: { 'Accept': 'application/json' },
    });
    check(response.status, 200);
  });

  // Test alerts endpoint
  group('Alerts API', () => {
    let response = http.get(`${API_BASE}/api/alerts`);
    check(response.status, 200);

    // Test with filters
    response = http.get(`${API_BASE}/api/alerts?severity=high&limit=10`, {
      headers: { 'Accept': 'application/json' },
    });
    check(response.status, 200);
  });

  // Test resources endpoint
  group('Resources API', () => {
    let response = http.get(`${API_BASE}/api/resources`);
    check(response.status, 200);

    // Test with status filter
    response = http.get(`${API_BASE}/api/resources?status=available`);
    check(response.status, 200);
  });

  // Test communication endpoint
  group('Communications API', () => {
    let response = http.get(`${API_BASE}/api/comms`);
    check(response.status, 200);
  });

  // Test risk assessments
  group('Risk API', () => {
    let response = http.get(`${API_BASE}/api/risk`);
    check(response.status, 200);

    // Test with time horizon
    response = http.get(`${API_BASE}/api/risk?timeHorizon=24h`);
    check(response.status, 200);
  });
}
```

Run load tests:
```bash
# Install k6
# For macOS: brew install k6
# For Ubuntu: apt-get install k6

# Run load test
k6 run load-test.js

# Run with HTML report
k6 run load-test.js --out html
```

## 📋 Test Data Management

### Test Database Setup

The database is automatically populated with test data. Key test data includes:

- **4 Zones**: Geographic areas with different characteristics
- **5 Assets**: Critical infrastructure in various zones
- **Multiple Risk Assessments**: Time-based predictions for different horizons
- **Sample Alerts**: Various severity levels and types
- **Emergency Resources**: Different types and statuses
- **Communications**: Sample messages across channels
- **River Gauges**: Monitoring stations with readings

### Test Data Reset

To reset test data between test runs:

```bash
# Stop containers
docker compose down

# Remove database volume
docker volume rm frontend_postgres_data

# Restart with fresh data
docker compose up --build
```

## 🔧 Test Environment Setup

### Database Connection

```bash
# Check database connection
curl http://localhost:8080/health

# Should return:
# {
#   "status": "ok",
#   "timestamp": "2025-11-13T12:30:00.000Z",
#   "database": "connected",
#   "version": "2.0.0"
# }
```

### Service Health Checks

```bash
# Check all services
docker compose ps

# Check backend logs
docker compose logs backend

# Check frontend logs
docker compose logs web
```

## 🚨 Common Issues & Solutions

### Connection Issues

**Problem**: API returns connection refused
**Solution**: Ensure backend container is running:
```bash
docker compose start backend
```

**Problem**: Database connection failed
**Solution**: Check PostgreSQL container:
```bash
docker compose start postgres
docker compose logs postgres
```

### Data Issues

**Problem**: Empty responses from endpoints
**Solution**: Check if database is populated:
```bash
# Check zones count
curl http://localhost:8080/api/zones | jq '.features | length'

# If 0, repopulate database
cd ../scripts && node populate-database.js
```

### CORS Issues

**Problem**: Cross-origin requests blocked
**Solution**: Check API server CORS configuration - it should be enabled in development mode.

### Timeout Issues

**Problem**: Requests timing out
**Solution**: Check database connection pool and server logs for performance issues.

---

**Last Updated**: 2025-11-13
**API Version**: 2.0.0