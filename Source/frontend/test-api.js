// Simple test to check API endpoints
const fetch = require('node-fetch');

async function testAPI() {
  console.log('Testing API endpoints...');

  try {
    // Test resources endpoint
    console.log('Testing /api/resources...');
    const resourcesResponse = await fetch('http://localhost:18080/api/resources');
    if (resourcesResponse.ok) {
      const resources = await resourcesResponse.json();
      console.log('✓ /api/resources works, found:', Object.keys(resources));
    } else {
      console.log('✗ /api/resources failed:', resourcesResponse.status);
    }

    // Test admin depots endpoint
    console.log('Testing /api/admin/resources/depots...');
    const depotsResponse = await fetch('http://localhost:18080/api/admin/resources/depots');
    if (depotsResponse.ok) {
      const depots = await depotsResponse.json();
      console.log('✓ /api/admin/resources/depots works, found depots:', depots.length);
    } else {
      console.log('✗ /api/admin/resources/depots failed:', depotsResponse.status);
    }

  } catch (error) {
    console.error('API test failed:', error.message);
  }
}

testAPI();
