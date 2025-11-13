# Administrator Setup Guide

This guide walks system administrators through the initial setup and configuration of the Flood Prediction System Administrator Portal.

## 🎯 Overview

The Administrator Setup Guide covers:
- Initial system configuration
- User account setup
- System threshold configuration
- Resource management setup
- Security configuration

## 📋 Prerequisites

Before beginning setup, ensure you have:

- Administrator-level access to the system
- Basic understanding of flood prediction concepts
- Information about your organization's emergency response structure
- User directory and contact information
- Geographic zone data (if available)

## 🚀 Initial Setup

### Step 1: Access the System

1. **Navigate to the Application**
   ```
   URL: http://your-domain.com
   ```

2. **Select Administrator Role**
   - Click the role selector
   - Choose "Administrator" from the dropdown

3. **Initial Login**
   ```
   Default Username: admin.flood
   Default Email: admin@floodsystem.gov
   Password: [provided during installation]
   ```

### Step 2: Secure Your Account

1. **Change Default Password**
   - Go to User Profile → Change Password
   - Create a strong password (12+ characters, mixed case, numbers, symbols)
   - Enable two-factor authentication if available

2. **Update Contact Information**
   - Verify email address and phone number
   - Set up notification preferences
   - Configure backup contact methods

### Step 3: Configure Basic Settings

1. **System Information**
   - Organization name and details
   - Time zone and date format
   - Language preferences
   - Emergency contact information

2. **Notification Settings**
   - Default alert recipients
   - Communication channels
   - Escalation procedures
   - After-hours contact information

## 👥 User Management Setup

### Step 1: Create Administrator Accounts

Create additional administrator accounts for your team:

1. **Navigate to User Management**
   - Click "Users" in the main menu
   - Select "Add New User"

2. **Administrator User Information**
   ```json
   {
     "username": "admin.johndoe",
     "email": "john.doe@agency.gov",
     "firstName": "John",
     "lastName": "Doe",
     "role": "Administrator",
     "department": "IT Department",
     "phone": "+1-555-0123",
     "location": "Central Office"
   }
   ```

3. **Assign Permissions**
   - Full system access
   - User management capabilities
   - Zone configuration access
   - Threshold management permissions

### Step 2: Create Role Accounts

Set up accounts for other user roles:

#### Planners
```json
{
  "username": "planner.smith",
  "email": "smith.planner@agency.gov",
  "role": "Planner",
  "department": "Emergency Planning",
  "zones": ["Z-ALFA", "Z-BRAVO"]
}
```

#### Coordinators
```json
{
  "username": "coordinator.garcia",
  "email": "garcia.coord@agency.gov",
  "role": "Coordinator",
  "department": "Operations",
  "zones": ["Z-CHARLIE", "Z-ECHO"]
}
```

#### Data Analysts
```json
{
  "username": "analyst.chen",
  "email": "chen.analyst@agency.gov",
  "role": "Data Analyst",
  "department": "Analytics",
  "zones": []
}
```

### Step 3: Configure User Groups (Optional)

For larger organizations, consider creating user groups:

1. **Department Groups**
   - IT Department
   - Emergency Management
   - Operations
   - Planning

2. **Functional Groups**
   - Response Teams
   - Support Staff
   - Management
   - External Partners

## 🗺️ Geographic Zone Setup

### Step 1: Import Zone Data

If you have existing geographic data:

1. **Prepare GeoJSON File**
   ```json
   {
     "type": "FeatureCollection",
     "features": [
       {
         "type": "Feature",
         "properties": {
           "id": "ZONE-001",
           "name": "Downtown District",
           "population": 15000,
           "critical_assets": ["Hospital", "School"]
         },
         "geometry": {
           "type": "Polygon",
           "coordinates": [[[-3.71, 40.41], [-3.70, 40.42], ...]]
         }
       }
     ]
   }
   ```

2. **Import Zones**
   - Go to Region Management
   - Click "Import GeoJSON"
   - Select your file and upload
   - Review and validate imported data

### Step 2: Manual Zone Creation

If creating zones manually:

1. **Access Zone Editor**
   - Navigate to Region Management
   - Click "Edit Zones"

2. **Draw Zone Boundaries**
   - Select drawing tool from toolbar
   - Click points to create polygon
   - Close polygon to complete zone

3. **Configure Zone Properties**
   ```json
   {
     "name": "Riverside North",
     "population": 12450,
     "critical_assets": ["Hospital HN1", "School SN3"],
     "admin_level": 10,
     "evacuation_routes": ["Highway 101", "River Road"]
   }
   ```

### Step 3: Validate Zones

1. **Check Zone Integrity**
   - Ensure complete coverage of service area
   - Verify no gaps or overlaps
   - Validate critical asset locations

2. **Test Zone Assignments**
   - Assign test users to zones
   - Verify access permissions
   - Test zone-specific features

## ⚙️ Threshold Configuration

### Step 1: Configure Risk Thresholds

Set up risk level classifications:

1. **Low Risk**
   ```json
   {
     "name": "Low Risk",
     "band": "Low",
     "minRisk": 0.0,
     "maxRisk": 0.25,
     "color": "#22c55e",
     "autoAlert": false
   }
   ```

2. **Moderate Risk**
   ```json
   {
     "name": "Moderate Risk",
     "band": "Moderate",
     "minRisk": 0.25,
     "maxRisk": 0.5,
     "color": "#f59e0b",
     "autoAlert": false
   }
   ```

3. **High Risk**
   ```json
   {
     "name": "High Risk",
     "band": "High",
     "minRisk": 0.5,
     "maxRisk": 0.75,
     "color": "#ef4444",
     "autoAlert": true
   }
   ```

4. **Severe Risk**
   ```json
   {
     "name": "Severe Risk",
     "band": "Severe",
     "minRisk": 0.75,
     "maxRisk": 1.0,
     "color": "#991b1b",
     "autoAlert": true
   }
   ```

### Step 2: Configure Gauge Thresholds

Set up water level monitoring:

1. **River Gauges**
   ```json
   {
     "gaugeId": "G-RIV-001",
     "gaugeName": "Main River Gauge",
     "alertThreshold": 3.5,
     "criticalThreshold": 4.2,
     "unit": "meters"
   }
   ```

2. **Stream Gauges**
   ```json
   {
     "gaugeId": "G-STR-012",
     "gaugeName": "Tributary Stream Gauge",
     "alertThreshold": 2.1,
     "criticalThreshold": 2.8,
     "unit": "meters"
   }
   ```

### Step 3: Configure Alert Rules

Set up automated alerting:

1. **Risk-Based Alerts**
   ```json
   {
     "name": "Flood Probability Alert",
     "triggerType": "Risk Threshold",
     "triggerValue": "Severe",
     "severity": "Severe",
     "enabled": true,
     "channels": ["SMS", "Email", "Dashboard"],
     "cooldownMinutes": 60
   }
   ```

2. **Gauge-Based Alerts**
   ```json
   {
     "name": "Rapid Water Rise",
     "triggerType": "Gauge Rate",
     "triggerValue": "0.5m/hour",
     "severity": "High",
     "enabled": true,
     "channels": ["SMS", "Dashboard"],
     "cooldownMinutes": 30
   }
   ```

## 🚚 Resource Management Setup

### Step 1: Configure Depots

Set up facility locations:

1. **Main Depot**
   ```json
   {
     "name": "Central Depot",
     "address": "123 Main Street, Central District",
     "manager": "John Martinez",
     "phone": "+1-555-0101",
     "operatingHours": "24/7",
     "capacity": 100,
     "zones": ["Z-ALFA", "Z-BRAVO"],
     "status": "active"
   }
   ```

2. **Satellite Depots**
   ```json
   {
     "name": "East Yard",
     "address": "456 Industrial Ave, East District",
     "manager": "Sarah Chen",
     "phone": "+1-555-0102",
     "operatingHours": "06:00-22:00",
     "capacity": 75,
     "zones": ["Z-CHARLIE"],
     "status": "active"
   }
   ```

### Step 2: Configure Equipment

Set up equipment inventory:

1. **Pumps**
   ```json
   {
     "type": "Pump",
     "subtype": "High-Capacity",
     "capacity_lps": 300,
     "depot": "D-CENTRAL",
     "status": "available",
     "manufacturer": "FloodGuard Pro",
     "model": "FG-300X"
   }
   ```

2. **Vehicles**
   ```json
   {
     "type": "Vehicle",
     "subtype": "Emergency Truck",
     "depot": "D-CENTRAL",
     "status": "available",
     "licensePlate": "FG-2024-001"
   }
   ```

3. **Supplies**
   ```json
   {
     "type": "Sandbags",
     "units": 800,
     "depot": "D-EAST",
     "status": "available",
     "material": "Polypropylene"
   }
   ```

### Step 3: Configure Response Crews

Set up emergency response teams:

1. **Alpha Crew**
   ```json
   {
     "name": "Alpha Crew",
     "leader": "Mark Rodriguez",
     "phone": "+1-555-0201",
     "teamSize": 6,
     "depot": "D-CENTRAL",
     "skills": ["pumping", "evacuation", "first_aid"],
     "certifications": ["Swift Water Rescue", "First Aid"],
     "status": "ready"
   }
   ```

## 🔐 Security Configuration

### Step 1: Password Policies

Set up strong password requirements:

1. **Minimum Requirements**
   - Length: 12 characters minimum
   - Complexity: Mixed case, numbers, symbols
   - History: No reuse of last 5 passwords
   - Expiration: 90-day rotation

2. **Account Lockout**
   - Attempts: 5 failed attempts
   - Lockout duration: 15 minutes
   - Admin unlock required: No

### Step 2: Session Management

Configure user session settings:

1. **Timeout Settings**
   - Idle timeout: 30 minutes
   - Maximum session: 8 hours
   - Remember me: 7 days

2. **Concurrent Sessions**
   - Maximum per user: 3
   - Force logout: Yes
   - Session notification: Enabled

### Step 3: Access Controls

Set up additional security measures:

1. **IP Restrictions** (Optional)
   - Allowed IP ranges: [Your organization's IP ranges]
   - VPN required: Yes for remote access
   - Geographic restrictions: [Allowed regions]

2. **Two-Factor Authentication**
   - Required roles: Administrator, Coordinator
   - Methods: SMS, Authenticator App
   - Backup codes: Yes

## 📊 Testing and Validation

### Step 1: User Access Testing

1. **Test Role-Based Access**
   - Verify each role can only access appropriate features
   - Test zone-based restrictions
   - Validate permission inheritance

2. **Test User Management**
   - Create test users for each role
   - Verify password reset functionality
   - Test account status changes

### Step 2: Threshold Testing

1. **Simulate Risk Levels**
   - Create test scenarios for each risk band
   - Verify automatic alert generation
   - Test notification channels

2. **Gauge Threshold Testing**
   - Simulate water level changes
   - Test gauge rate alerts
   - Verify critical notifications

### Step 3: Resource Management Testing

1. **Equipment Deployment**
   - Test equipment assignment to crews
   - Verify status updates
   - Test maintenance scheduling

2. **Crew Assignment**
   - Test crew deployment to zones
   - Verify skill matching
   - Test availability tracking

## 🎯 Go-Live Checklist

### Pre-Launch Checklist

- [ ] All administrator accounts created and tested
- [ ] Zone configuration complete and validated
- [ ] Risk thresholds configured and tested
- [ ] Gauge thresholds set and validated
- [ ] Alert rules configured and tested
- [ ] Resource inventory complete
- [ ] Response crews configured and trained
- [ ] Security settings configured
- [ ] Backup procedures tested
- [ ] User training completed

### Launch Day Tasks

- [ ] Monitor system performance
- [ ] Verify all users can log in
- [ ] Test alert notifications
- [ ] Validate data synchronization
- [ ] Check backup processes
- [ ] Monitor error logs
- [ ] Support team on standby

### Post-Launch Monitoring

- [ ] System performance metrics
- [ ] User activity monitoring
- [ ] Alert effectiveness tracking
- [ ] Resource utilization tracking
- [ ] Security event monitoring

## 📞 Support Resources

### Documentation
- Complete User Guide: [Administrator Guide](README.md)
- API Documentation: [Admin API](../api/admin-endpoints.md)
- Troubleshooting Guide: [Support Section](README.md#troubleshooting)

### Training Resources
- Video Tutorials: [Training Portal](https://training.floodsystem.gov)
- Live Webinars: Monthly administrator training
- Knowledge Base: [Support Portal](https://support.floodsystem.gov)

### Support Contacts
- Technical Support: 1-800-FLOOD-TECH
- Emergency Support: 1-800-FLOOD-HELP
- Email Support: admin-support@floodsystem.gov

---

For additional assistance or questions, please refer to the complete [Administrator Documentation](README.md) or contact your system administrator.