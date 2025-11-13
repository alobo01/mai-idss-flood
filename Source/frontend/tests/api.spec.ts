import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Start with a clean page for API tests
    await page.goto('/planner/map');
    await page.waitForLoadState('networkidle');
  });

  test('Mock API endpoints are accessible', async ({ request }) => {
    // Test all API endpoints directly
    const endpoints = [
      '/api/zones',
      '/api/risk?at=2025-11-11T12:00:00Z',
      '/api/damage-index',
      '/api/resources',
      '/api/plan',
      '/api/alerts',
      '/api/comms',
      '/api/gauges',
    ];

    for (const endpoint of endpoints) {
      const response = await request.get(`http://localhost:8080${endpoint}`);
      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toBeDefined();
      expect(typeof data).toBe('object');
    }
  });

  test('API endpoints return valid JSON data', async ({ request }) => {
    // Test zones endpoint
    const zonesResponse = await request.get('http://localhost:8080/api/zones');
    const zonesData = await zonesResponse.json();
    expect(zonesData.type).toBe('FeatureCollection');
    expect(Array.isArray(zonesData.features)).toBe(true);

    // Test risk endpoint
    const riskResponse = await request.get('http://localhost:8080/api/risk?at=2025-11-11T12:00:00Z');
    const riskData = await riskResponse.json();
    expect(Array.isArray(riskData)).toBe(true);
    expect(riskData[0]).toHaveProperty('zoneId');
    expect(riskData[0]).toHaveProperty('risk');

    // Test resources endpoint
    const resourcesResponse = await request.get('http://localhost:8080/api/resources');
    const resourcesData = await resourcesResponse.json();
    expect(resourcesData).toHaveProperty('depots');
    expect(resourcesData).toHaveProperty('equipment');
    expect(resourcesData).toHaveProperty('crews');

    // Test alerts endpoint
    const alertsResponse = await request.get('http://localhost:8080/api/alerts');
    const alertsData = await alertsResponse.json();
    expect(Array.isArray(alertsData)).toBe(true);
    expect(alertsData[0]).toHaveProperty('id');
    expect(alertsData[0]).toHaveProperty('severity');
  });

  test('API CORS headers are properly set', async ({ request }) => {
    const response = await request.get('http://localhost:8080/api/zones');

    // Check for CORS headers
    const corsHeaders = {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'access-control-allow-headers': 'Content-Type, Authorization',
    };

    for (const [header, expectedValue] of Object.entries(corsHeaders)) {
      const actualValue = response.headers()[header];
      expect(actualValue).toBe(expectedValue);
    }
  });

  test('API POST endpoints work', async ({ request }) => {
    // Test alert acknowledgement
    const ackResponse = await request.post('http://localhost:8080/api/alerts/A-1001/ack');
    expect(ackResponse.status()).toBe(200);

    const ackData = await ackResponse.json();
    expect(ackData.success).toBe(true);

    // Test communication endpoint
    const commResponse = await request.post('http://localhost:8080/api/comms', {
      data: {
        channel: 'global',
        from: 'Test User',
        text: 'Test communication message'
      }
    });
    expect(commResponse.status()).toBe(200);

    const commData = await commResponse.json();
    expect(commData.success).toBe(true);
    expect(commData.text).toBe('Test communication message');
  });

  test('API health check endpoint', async ({ request }) => {
    const response = await request.get('http://localhost:8080/health');
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.status).toBe('ok');
    expect(data.timestamp).toBeDefined();
  });

  test('API error handling for missing files', async ({ request }) => {
    // Test non-existent risk file
    const response = await request.get('http://localhost:8080/api/risk?at=non-existent-timestamp');
    expect(response.status()).toBe(200); // Should fallback to default file

    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

});