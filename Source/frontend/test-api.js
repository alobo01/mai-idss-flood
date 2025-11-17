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

    // Test admin users endpoint
    console.log('Testing /api/admin/users...');
    const usersResponse = await fetch('http://localhost:18080/api/admin/users');
    if (usersResponse.ok) {
      const users = await usersResponse.json();
      console.log('✓ /api/admin/users works, found users:', users.length);
    } else {
      console.log('✗ /api/admin/users failed:', usersResponse.status);
    }

  } catch (error) {
    console.error('API test failed:', error.message);
  }
}

testAPI();