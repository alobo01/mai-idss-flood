# API Endpoints Reference

Complete documentation for all Flood Prediction API endpoints with request/response examples and parameters.

## 🏥 Health & System Endpoints

### Health Check
**GET** `/health`

Check API health and database connectivity status.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-13T12:30:00.000Z",
  "database": "connected",
  "version": "2.0.0"
}
```

**Status Codes:**
- `200` - System healthy
- `500` - System unhealthy or database connection failed

---

## 🗺️ Geographic Data Endpoints

### Get All Zones
**GET** `/api/zones`

Retrieve all flood zones as GeoJSON FeatureCollection.

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-3.71, 40.41], [-3.70, 40.41], [-3.70, 40.42], [-3.71, 40.42], [-3.71, 40.41]]]
      },
      "properties": {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "Riverside North",
        "description": "Northern riverside residential area",
        "population": 12450,
        "area_km2": 15.2
      }
    }
  ]
}
```

### Get Assets
**GET** `/api/assets?zoneId={zoneId}`

Retrieve critical infrastructure assets with optional zone filtering.

**Parameters:**
- `zoneId` (optional, string, UUID) - Filter assets by zone

**Response:**
```json
[
  {
    "id": "10000000-0000-0000-0000-000000000001",
    "zoneId": "00000000-0000-0000-0000-000000000001",
    "zoneName": "Riverside North",
    "name": "Hospital HN1",
    "type": "hospital",
    "criticality": "critical",
    "location": {
      "type": "Point",
      "coordinates": [-3.705, 40.415]
    },
    "address": "123 Riverside Ave",
    "capacity": 200,
    "metadata": {
      "emergency_services": true,
      "floors": 5
    }
  }
]
```

---

## ⚠️ Risk Assessment Endpoints

### Get Risk Assessments
**GET** `/api/risk?at={timestamp}&timeHorizon={horizon}`

Retrieve risk assessments for specific time and forecast horizon.

**Parameters:**
- `at` (optional, string) - Forecast timestamp (ISO 8601 or hyphenated format)
  - Default: Current time + 12 hours
  - Example: "2025-11-11T12:00:00Z" or "2025-11-11T12-00-00Z"
- `timeHorizon` (optional, string) - Forecast time horizon
  - Default: "12h"
  - Options: "6h", "12h", "18h", "24h", "48h", "72h"

**Response:**
```json
{
  "00000000-0000-0000-0000-000000000001": {
    "riskLevel": 0.75,
    "timeHorizon": "12h",
    "forecastTime": "2025-11-13T23:00:00.000Z",
    "zoneName": "Riverside North",
    "population": 12450,
    "areaKm2": 15.2,
    "riskFactors": {
      "precipitation": 45.2,
      "riverLevel": 3.8,
      "soilSaturation": 87,
      "temperature": 15.5
    }
  }
}
```

### Get Damage Index
**GET** `/api/damage-index?zoneId={zoneId}&assetType={type}`

Retrieve damage assessments and index calculations.

**Parameters:**
- `zoneId` (optional, string, UUID) - Filter by zone ID
- `assetType` (optional, string) - Filter by asset type
  - Options: "hospital", "school", "power_plant", "bridge", "road", "water_treatment"

**Response:**
```json
[
  {
    "zoneId": "00000000-0000-0000-0000-000000000001",
    "zoneName": "Riverside North",
    "damageIndex": 25,
    "totalAssets": 15,
    "damagedAssets": 3,
    "estimatedCost": 150000.50,
    "assessments": [
      {
        "assetId": "10000000-0000-0000-0000-000000000001",
        "assetName": "Main Bridge",
        "assetType": "bridge",
        "damageLevel": 0.3,
        "damageType": "structural",
        "estimatedCost": 50000.00,
        "status": "assessed",
        "assessmentTime": "2025-11-13T09:30:00.000Z"
      }
    ]
  }
]
```

---

## 🚨 Alert Management Endpoints

### Get Alerts
**GET** `/api/alerts?severity={level}&acknowledged={bool}&zoneId={zoneId}&limit={count}`

Retrieve system alerts with comprehensive filtering options.

**Parameters:**
- `severity` (optional, string) - Filter by severity level
  - Options: "low", "medium", "high", "critical"
- `acknowledged` (optional, boolean) - Filter by acknowledgment status
- `zoneId` (optional, string, UUID) - Filter by zone ID
- `limit` (optional, integer) - Maximum number of alerts to return
  - Default: 50
  - Maximum: 500

**Response:**
```json
[
  {
    "id": "30000000-0000-0000-0000-000000000001",
    "zoneId": "00000000-0000-0000-0000-000000000001",
    "zoneName": "Riverside North",
    "severity": "high",
    "alertType": "flood_warning",
    "title": "Flood Warning - Riverside North",
    "message": "River levels rising rapidly. Prepare for possible evacuation.",
    "acknowledged": false,
    "acknowledgedBy": null,
    "acknowledgedAt": null,
    "resolved": false,
    "resolvedAt": null,
    "metadata": {
      "source": "river_gauge",
      "threshold_exceeded": true
    },
    "createdAt": "2025-11-13T10:00:00.000Z"
  }
]
```

### Acknowledge Alert
**POST** `/api/alerts/{id}/ack`

Mark an alert as acknowledged.

**Path Parameters:**
- `id` (required, string, UUID) - Alert ID

**Request Body:**
```json
{
  "acknowledgedBy": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Alert acknowledged successfully",
  "alert": {
    "id": "30000000-0000-0000-0000-000000000001",
    "acknowledged": true,
    "acknowledgedBy": "John Doe",
    "acknowledgedAt": "2025-11-13T10:15:00.000Z"
  }
}
```

**Status Codes:**
- `200` - Alert acknowledged successfully
- `404` - Alert not found
- `500` - Server error

---

## 📡 Communication Endpoints

### Get Communications
**GET** `/api/comms?channel={type}&priority={level}&limit={count}`

Retrieve communication logs with filtering options.

**Parameters:**
- `channel` (optional, string) - Filter by communication channel
  - Options: "sms", "email", "radio", "phone", "social", "public"
- `priority` (optional, string) - Filter by priority level
  - Options: "low", "normal", "high", "urgent"
- `limit` (optional, integer) - Maximum number of communications to return
  - Default: 100
  - Maximum: 1000

**Response:**
```json
[
  {
    "id": "40000000-0000-0000-0000-000000000001",
    "channel": "sms",
    "sender": "Emergency Command Center",
    "recipient": "All Zone Residents",
    "message": "Evacuation order issued for Riverside North",
    "direction": "outbound",
    "priority": "high",
    "status": "sent",
    "metadata": {
      "delivery_attempts": 1,
      "response_received": false
    },
    "createdAt": "2025-11-13T10:15:00.000Z"
  }
]
```

### Send Communication
**POST** `/api/comms`

Create a new communication record.

**Request Body:**
```json
{
  "channel": "sms",
  "from": "Emergency Command Center",
  "to": "All Zone Residents",
  "message": "Evacuation order issued for Riverside North",
  "direction": "outbound",
  "priority": "high"
}
```

**Required Fields:**
- `channel` - Communication channel
- `from` - Sender information
- `to` - Recipient information
- `message` - Message content

**Optional Fields:**
- `direction` - "inbound" or "outbound" (default: "outbound")
- `priority` - Priority level (default: "normal")

**Response:**
```json
{
  "success": true,
  "communication": {
    "id": "40000000-0000-0000-0000-000000000002",
    "channel": "sms",
    "sender": "Emergency Command Center",
    "recipient": "All Zone Residents",
    "message": "Evacuation order issued for Riverside North",
    "direction": "outbound",
    "priority": "high",
    "status": "sent",
    "createdAt": "2025-11-13T10:20:00.000Z"
  }
}
```

**Status Codes:**
- `201` - Communication created successfully
- `400` - Invalid request data
- `500` - Server error

---

## 🛠️ Resource Management Endpoints

### Get Resources
**GET** `/api/resources?status={state}&type={category}`

Retrieve emergency resources with deployment status.

**Parameters:**
- `status` (optional, string) - Filter by resource status
  - Options: "available", "deployed", "standby", "maintenance"
- `type` (optional, string) - Filter by resource type
  - Options: "emergency_crew", "fire_crew", "medical_crew", "engineering_crew", "equipment"

**Response:**
```json
[
  {
    "id": "20000000-0000-0000-0000-000000000001",
    "name": "Emergency Team Alpha",
    "type": "emergency_crew",
    "status": "available",
    "location": {
      "type": "Point",
      "coordinates": [-3.695, 40.405]
    },
    "capacity": 12,
    "capabilities": ["medical", "rescue", "evacuation"],
    "contactInfo": {
      "phone": "+1-555-0001",
      "email": "alpha@emergency.gov"
    },
    "deployment": null
  },
  {
    "id": "20000000-0000-0000-0000-000000000002",
    "name": "Engineering Unit Beta",
    "type": "engineering_crew",
    "status": "deployed",
    "deployment": {
      "zoneId": "00000000-0000-0000-0000-000000000001",
      "zoneName": "Riverside North",
      "deploymentTime": "2025-11-13T08:00:00.000Z",
      "returnTime": "2025-11-13T18:00:00.000Z"
    }
  }
]
```

---

## 🌡️ Monitoring Endpoints

### Get River Gauges
**GET** `/api/gauges?status={state}`

Retrieve river gauge monitoring data with recent readings.

**Parameters:**
- `status` (optional, string) - Filter by gauge status
  - Options: "active", "inactive", "maintenance", "error"

**Response:**
```json
[
  {
    "id": "50000000-0000-0000-0000-000000000001",
    "name": "River Gauge RG01",
    "location": {
      "type": "Point",
      "coordinates": [-3.700, 40.420]
    },
    "riverName": "Manzanares River",
    "gaugeType": "water_level",
    "unit": "meters",
    "alertThreshold": 4.5,
    "warningThreshold": 3.5,
    "status": "active",
    "recentReadings": [
      {
        "readingValue": 3.2,
        "readingTime": "2025-11-13T10:00:00.000Z",
        "qualityFlag": "good"
      },
      {
        "readingValue": 3.1,
        "readingTime": "2025-11-13T09:30:00.000Z",
        "qualityFlag": "good"
      }
    ],
    "metadata": {
      "elevation": 650.5,
      "basin": "Manzanares Basin"
    }
  }
]
```

---

## 📋 Response Plans

### Get Response Plans
**GET** `/api/plan?status={state}&type={category}`

Retrieve emergency response plans and procedures.

**Parameters:**
- `status` (optional, string) - Filter by plan status
  - Options: "draft", "active", "archived"
- `type` (optional, string) - Filter by plan type
  - Options: "evacuation", "shelter", "medical", "infrastructure", "communication"

**Response:**
```json
[
  {
    "id": "60000000-0000-0000-0000-000000000001",
    "name": "Zone Evacuation Plan - Riverside North",
    "description": "Comprehensive evacuation plan for Riverside North zone",
    "type": "evacuation",
    "triggerConditions": ["river_level > 4.0m", "rainfall > 50mm/24h"],
    "recommendedActions": [
      "Issue evacuation order",
      "Open emergency shelters",
      "Deploy rescue teams"
    ],
    "requiredResources": [
      "emergency_crews",
      "transportation",
      "medical_supplies"
    ],
    "estimatedDuration": "6-12 hours",
    "priority": "high",
    "status": "active",
    "createdAt": "2025-10-01T08:00:00.000Z",
    "updatedAt": "2025-11-01T14:30:00.000Z"
  }
]
```

---

## 📊 Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error description",
  "details": "Detailed error information (development only)"
}
```

**Common Error Codes:**
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error (database or system error)

---

## 🧪 Testing Examples

### Using curl

```bash
# Health check
curl http://localhost:18080/health

# Get all zones
curl http://localhost:18080/api/zones

# Get high-severity alerts
curl "http://localhost:18080/api/alerts?severity=high"

# Get available resources
curl "http://localhost:18080/api/resources?status=available"

# Acknowledge an alert
curl -X POST http://localhost:18080/api/alerts/30000000-0000-0000-0000-000000000001/ack \
  -H "Content-Type: application/json" \
  -d '{"acknowledgedBy":"John Doe"}'

# Send communication
curl -X POST http://localhost:18080/api/comms \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms",
    "from": "Emergency Command",
    "to": "Zone Residents",
    "message": "Test message",
    "priority": "high"
  }'
```

### Using JavaScript/TypeScript

```typescript
// API Client Example
class FloodPredictionAPI {
  private baseUrl = 'http://localhost:18080';

  async getZones() {
    const response = await fetch(`${this.baseUrl}/api/zones`);
    return response.json();
  }

  async getAlerts(severity?: string) {
    const url = severity
      ? `${this.baseUrl}/api/alerts?severity=${severity}`
      : `${this.baseUrl}/api/alerts`;
    const response = await fetch(url);
    return response.json();
  }

  async acknowledgeAlert(alertId: string, acknowledgedBy: string) {
    const response = await fetch(`${this.baseUrl}/api/alerts/${alertId}/ack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ acknowledgedBy })
    });
    return response.json();
  }
}
```

---

## 📈 Rate Limiting & Performance

### Current Limits
- No rate limiting (development mode)
- Connection pooling: 20 maximum connections
- Query timeout: 30 seconds
- Response size: Optimized with pagination where applicable

### Performance Tips
- Use zone-based filtering to reduce data transfer
- Implement client-side caching for static reference data
- Use pagination for large datasets
- Batch multiple requests when possible

---

## 🔗 Related Documentation

- **[Database Schema](database.md)** - Complete database structure
- **[API Testing](testing.md)** - Testing strategies and examples
- **[API Reference](reference.md)** - Swagger UI details
- **[Deployment Guide](../deployment.md)** - Production deployment