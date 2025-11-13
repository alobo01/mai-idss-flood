# Administrator API Reference

This document provides comprehensive documentation for all Administrator API endpoints in the Flood Prediction System.

## 📋 Overview

The Administrator API provides programmatic access to all system management functions, including user management, resource configuration, threshold settings, and zone management.

## 🔗 Base URL

```
Production: https://your-domain.com/api/admin
Development: http://localhost:8080/api/admin
```

## 🔐 Authentication

All Administrator API endpoints require JWT authentication:

```http
Authorization: Bearer <admin-jwt-token>
Content-Type: application/json
```

### Authentication Flow

1. **Login to obtain token:**
   ```http
   POST /api/auth/login
   {
     "username": "admin.flood",
     "password": "your-password"
   }
   ```

2. **Use token in subsequent requests:**
   ```http
   GET /api/admin/users
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## 👥 User Management Endpoints

### Get All Users
Retrieve all user accounts in the system.

```http
GET /api/admin/users
```

**Response:**
```json
[
  {
    "id": "USR-001",
    "username": "admin.flood",
    "email": "admin@floodsystem.gov",
    "firstName": "Sarah",
    "lastName": "Johnson",
    "role": "Administrator",
    "department": "System Administration",
    "phone": "+1-555-0101",
    "location": "Central Office",
    "status": "active",
    "lastLogin": "2025-11-13T09:30:00Z",
    "zones": ["Z-ALFA", "Z-BRAVO", "Z-CHARLIE", "Z-ECHO"],
    "permissions": ["system_config", "user_management", "threshold_management"],
    "createdAt": "2024-01-15T10:00:00Z"
  }
]
```

### Create User
Create a new user account.

```http
POST /api/admin/users
```

**Request Body:**
```json
{
  "username": "planner.smith",
  "email": "m.smith@floodsystem.gov",
  "firstName": "Michael",
  "lastName": "Smith",
  "role": "Planner",
  "department": "Emergency Planning",
  "phone": "+1-555-0102",
  "location": "Regional Office North",
  "status": "active",
  "zones": ["Z-ALFA", "Z-BRAVO"]
}
```

**Response (201 Created):**
```json
{
  "id": "USR-002",
  "username": "planner.smith",
  "email": "m.smith@floodsystem.gov",
  "firstName": "Michael",
  "lastName": "Smith",
  "role": "Planner",
  "department": "Emergency Planning",
  "phone": "+1-555-0102",
  "location": "Regional Office North",
  "status": "active",
  "zones": ["Z-ALFA", "Z-BRAVO"],
  "permissions": ["risk_assessment", "scenario_planning", "alert_management"],
  "createdAt": "2025-11-13T10:00:00Z",
  "lastLogin": null
}
```

### Update User
Update an existing user account.

```http
PUT /api/admin/users/{id}
```

**Request Body:**
```json
{
  "email": "michael.smith@floodsystem.gov",
  "phone": "+1-555-0103",
  "location": "Central Office",
  "status": "active",
  "zones": ["Z-ALFA", "Z-BRAVO", "Z-CHARLIE"]
}
```

### Delete User
Delete a user account.

```http
DELETE /api/admin/users/{id}
```

**Response (204 No Content)**

## ⚙️ Threshold Management Endpoints

### Risk Thresholds

#### Get Risk Thresholds
Retrieve all risk threshold configurations.

```http
GET /api/admin/thresholds/risk
```

**Response:**
```json
[
  {
    "id": "RT-001",
    "name": "Low Risk",
    "band": "Low",
    "minRisk": 0,
    "maxRisk": 0.25,
    "color": "#22c55e",
    "description": "Normal operating conditions",
    "autoAlert": false
  },
  {
    "id": "RT-002",
    "name": "Moderate Risk",
    "band": "Moderate",
    "minRisk": 0.25,
    "maxRisk": 0.5,
    "color": "#f59e0b",
    "description": "Monitor closely, prepare for potential action",
    "autoAlert": false
  }
]
```

#### Create Risk Threshold
Create a new risk threshold.

```http
POST /api/admin/thresholds/risk
```

**Request Body:**
```json
{
  "name": "Elevated Risk",
  "band": "Moderate",
  "minRisk": 0.3,
  "maxRisk": 0.6,
  "color": "#f59e0b",
  "description": "Elevated risk conditions",
  "autoAlert": true
}
```

#### Update Risk Threshold
Update an existing risk threshold.

```http
PUT /api/admin/thresholds/risk/{id}
```

**Request Body:**
```json
{
  "name": "Updated Risk Level",
  "minRisk": 0.35,
  "maxRisk": 0.65,
  "autoAlert": true
}
```

#### Delete Risk Threshold
Delete a risk threshold.

```http
DELETE /api/admin/thresholds/risk/{id}
```

### Gauge Thresholds

#### Get Gauge Thresholds
Retrieve all gauge threshold configurations.

```http
GET /api/admin/thresholds/gauges
```

**Response:**
```json
[
  {
    "id": "GT-001",
    "gaugeId": "G-RIV-12",
    "gaugeName": "Main River Gauge",
    "alertThreshold": 3.5,
    "criticalThreshold": 4.2,
    "unit": "meters",
    "description": "Primary river level monitoring"
  }
]
```

#### Create Gauge Threshold
Create a new gauge threshold.

```http
POST /api/admin/thresholds/gauges
```

**Request Body:**
```json
{
  "gaugeId": "G-STR-08",
  "gaugeName": "Stream Junction A",
  "alertThreshold": 2.1,
  "criticalThreshold": 2.8,
  "unit": "meters",
  "description": "Tributary stream monitoring point"
}
```

#### Update Gauge Threshold
Update an existing gauge threshold.

```http
PUT /api/admin/thresholds/gauges/{id}
```

#### Delete Gauge Threshold
Delete a gauge threshold.

```http
DELETE /api/admin/thresholds/gauges/{id}
```

### Alert Rules

#### Get Alert Rules
Retrieve all alert rule configurations.

```http
GET /api/admin/alerts/rules
```

**Response:**
```json
[
  {
    "id": "AR-001",
    "name": "Flood Probability Alert",
    "triggerType": "Risk Threshold",
    "triggerValue": "Severe",
    "severity": "Severe",
    "enabled": true,
    "channels": ["SMS", "Email", "Dashboard"],
    "cooldownMinutes": 60,
    "description": "Alert when flood probability exceeds severe threshold"
  }
]
```

#### Create Alert Rule
Create a new alert rule.

```http
POST /api/admin/alerts/rules
```

**Request Body:**
```json
{
  "name": "Critical Water Level",
  "triggerType": "Gauge Level",
  "triggerValue": "4.0",
  "severity": "High",
  "enabled": true,
  "channels": ["SMS", "Dashboard"],
  "cooldownMinutes": 30,
  "description": "Alert when water level reaches critical threshold"
}
```

#### Update Alert Rule
Update an existing alert rule.

```http
PUT /api/admin/alerts/rules/{id}
```

#### Delete Alert Rule
Delete an alert rule.

```http
DELETE /api/admin/alerts/rules/{id}
```

## 🚚 Resource Management Endpoints

### Depot Management

#### Get All Depots
Retrieve all depot configurations.

```http
GET /api/admin/resources/depots
```

**Response:**
```json
[
  {
    "id": "D-CENTRAL",
    "name": "Central Depot",
    "address": "123 Main Street, Central District",
    "manager": "John Martinez",
    "phone": "+1-555-0101",
    "operatingHours": "24/7",
    "capacity": 100,
    "zones": ["Z-ALFA", "Z-BRAVO"],
    "status": "active",
    "lat": 40.4167,
    "lng": -3.7033
  }
]
```

#### Create Depot
Create a new depot.

```http
POST /api/admin/resources/depots
```

**Request Body:**
```json
{
  "name": "North Facility",
  "address": "456 North Avenue, North District",
  "manager": "Sarah Chen",
  "phone": "+1-555-0110",
  "operatingHours": "06:00-22:00",
  "capacity": 80,
  "zones": ["Z-ALFA"],
  "status": "active"
}
```

#### Update Depot
Update an existing depot.

```http
PUT /api/admin/resources/depots/{id}
```

#### Delete Depot
Delete a depot.

```http
DELETE /api/admin/resources/depots/{id}
```

### Equipment Management

#### Get All Equipment
Retrieve all equipment inventory.

```http
GET /api/admin/resources/equipment
```

**Response:**
```json
[
  {
    "id": "P-001",
    "type": "Pump",
    "subtype": "High-Capacity",
    "capacity_lps": 300,
    "depot": "D-CENTRAL",
    "status": "available",
    "serialNumber": "PMP-001-2024",
    "manufacturer": "FloodGuard Pro",
    "model": "FG-300X"
  }
]
```

#### Create Equipment
Create new equipment record.

```http
POST /api/admin/resources/equipment
```

**Request Body:**
```json
{
  "type": "Vehicle",
  "subtype": "Emergency Truck",
  "depot": "D-CENTRAL",
  "status": "available",
  "licensePlate": "FG-2024-003",
  "vin": "1HGCM82633A004352"
}
```

#### Update Equipment
Update existing equipment.

```http
PUT /api/admin/resources/equipment/{id}
```

#### Delete Equipment
Delete equipment record.

```http
DELETE /api/admin/resources/equipment/{id}
```

### Crew Management

#### Get All Crews
Retrieve all response crews.

```http
GET /api/admin/resources/crews
```

**Response:**
```json
[
  {
    "id": "C-A1",
    "name": "Alpha Crew",
    "leader": "Mark Rodriguez",
    "phone": "+1-555-0201",
    "teamSize": 6,
    "depot": "D-CENTRAL",
    "status": "ready",
    "skills": ["pumping", "evacuation", "first_aid"],
    "certifications": ["Swift Water Rescue", "First Aid"],
    "experience": "5 years"
  }
]
```

#### Create Crew
Create new response crew.

```http
POST /api/admin/resources/crews
```

**Request Body:**
```json
{
  "name": "Echo Crew",
  "leader": "Jennifer Liu",
  "phone": "+1-555-0205",
  "teamSize": 8,
  "depot": "D-EAST",
  "status": "ready",
  "skills": ["rescue", "medical", "evacuation"],
  "certifications": ["Technical Rescue", "EMT"],
  "experience": "4 years"
}
```

#### Update Crew
Update existing crew.

```http
PUT /api/admin/resources/crews/{id}
```

#### Delete Crew
Delete crew record.

```http
DELETE /api/admin/resources/crews/{id}
```

## 🗺️ Zone Management Endpoints

### Update Zones
Update geographic zone configuration with GeoJSON data.

```http
PUT /api/admin/zones
```

**Request Body:**
```json
{
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "properties": {
          "id": "Z-NEW",
          "name": "New Zone",
          "population": 15000,
          "critical_assets": ["Hospital", "School"],
          "admin_level": 10
        },
        "geometry": {
          "type": "Polygon",
          "coordinates": [[
            [-3.71, 40.41],
            [-3.70, 40.41],
            [-3.70, 40.42],
            [-3.71, 40.42],
            [-3.71, 40.41]
          ]]
        }
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "zones": {
    "type": "FeatureCollection",
    "features": [...]
  }
}
```

## 📊 Export Endpoints

### Export Users
Export all user data.

```http
GET /api/admin/export/users
```

**Response:**
```json
{
  "users": [
    {
      "id": "USR-001",
      "username": "admin.flood",
      "email": "admin@floodsystem.gov",
      "role": "Administrator",
      "status": "active",
      "createdAt": "2024-01-15T10:00:00Z"
    }
  ],
  "exported_at": "2025-11-13T10:00:00Z",
  "total_count": 5
}
```

### Export Thresholds
Export all threshold configurations.

```http
GET /api/admin/export/thresholds
```

**Response:**
```json
{
  "risk": [...],
  "gauges": [...],
  "alerts": [...],
  "exported_at": "2025-11-13T10:00:00Z"
}
```

### Export Resources
Export all resource configurations.

```http
GET /api/admin/export/resources
```

**Response:**
```json
{
  "depots": [...],
  "equipment": [...],
  "crews": [...],
  "exported_at": "2025-11-13T10:00:00Z"
}
```

### Export Zones
Export zone configuration as GeoJSON.

```http
GET /api/admin/export/zones
```

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [...],
  "exported_at": "2025-11-13T10:00:00Z"
}
```

## 🚨 Error Responses

### Standard Error Format

All API endpoints return errors in a consistent format:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {
    "field": "validation_error_message"
  },
  "timestamp": "2025-11-13T10:00:00Z"
}
```

### Common Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request data or validation error |
| 401 | Unauthorized | Invalid or missing authentication token |
| 403 | Forbidden | Insufficient permissions for the operation |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (duplicate data) |
| 422 | Unprocessable Entity | Validation failed for request data |
| 500 | Internal Server Error | Server-side error |

### Validation Error Examples

```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "email": "Invalid email format",
    "teamSize": "Team size must be between 1 and 20"
  },
  "timestamp": "2025-11-13T10:00:00Z"
}
```

## 🔧 Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Standard Endpoints**: 100 requests per minute
- **Bulk Operations**: 10 requests per minute
- **Export Operations**: 5 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 📝 Examples and Use Cases

### Creating a Complete User Setup

```bash
# 1. Create a new planner user
curl -X POST http://localhost:8080/api/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "planner.jane",
    "email": "jane.planner@agency.gov",
    "firstName": "Jane",
    "lastName": "Smith",
    "role": "Planner",
    "department": "Emergency Planning",
    "status": "active",
    "zones": ["Z-ALFA", "Z-BRAVO"]
  }'

# 2. Create equipment for the user's zones
curl -X POST http://localhost:8080/api/admin/resources/equipment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Pump",
    "subtype": "Portable",
    "capacity_lps": 250,
    "depot": "D-EAST",
    "status": "available"
  }'

# 3. Set up alert rules for their zones
curl -X POST http://localhost:8080/api/admin/alerts/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Zone Risk Alert",
    "triggerType": "Risk Threshold",
    "triggerValue": "High",
    "severity": "High",
    "enabled": true,
    "channels": ["Email", "Dashboard"],
    "cooldownMinutes": 60
  }'
```

### Bulk Configuration Setup

```bash
# Export current configuration
curl -X GET http://localhost:8080/api/admin/export/thresholds \
  -H "Authorization: Bearer $TOKEN" \
  -o thresholds_backup.json

# Update thresholds in bulk
cat new_thresholds.json | jq '.risk[]' | while read threshold; do
  curl -X POST http://localhost:8080/api/admin/thresholds/risk \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$threshold"
done
```

## 🧪 Testing the API

### Health Check
Verify the API is running:

```bash
curl http://localhost:8080/health
```

### Authentication Test
Test authentication:

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin.flood", "password": "password"}' \
  | jq -r '.token')

# Test authenticated request
curl -X GET http://localhost:8080/api/admin/users \
  -H "Authorization: Bearer $TOKEN"
```

### Postman Collection

A Postman collection is available for testing all Administrator API endpoints:

[Download Administrator API Collection](./postman/admin-api-collection.json)

## 📞 Support

For API-related issues or questions:

- **Technical Documentation**: [API Overview](README.md)
- **Support Email**: api-support@floodsystem.gov
- **Status Page**: https://status.floodsystem.gov
- **Developer Portal**: https://developers.floodsystem.gov

---

For additional information about using the Administrator API, please refer to the [Administrator Setup Guide](../administrator/setup.md) or contact your system administrator.