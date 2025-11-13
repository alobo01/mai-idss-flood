# Administrator Portal Documentation

Welcome to the comprehensive documentation for the Flood Prediction System Administrator Portal. This portal provides complete database management capabilities for non-technical users to administer all aspects of the flood prediction system.

## 📋 Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Core Features](#core-features)
- [User Guide](#user-guide)
- [Security](#security)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Administrator portal is designed specifically for non-technical users who need to manage the flood prediction system's database and configuration. The interface provides:

- **Intuitive Forms**: User-friendly interfaces for all data management tasks
- **Visual Feedback**: Clear indicators for status, validation, and errors
- **Comprehensive Management**: Complete CRUD operations for all system entities
- **Security**: Role-based access control with proper validation
- **Audit Support**: Change tracking and data integrity

### Target Users

- **System Administrators**: IT staff responsible for system maintenance
- **Emergency Managers**: Personnel overseeing emergency operations
- **Data Managers**: Staff maintaining system data and configurations
- **Policy Administrators**: Users managing thresholds and alert rules

## 🚀 Getting Started

### Prerequisites

- Administrator account with system access
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Basic computer literacy

### Initial Setup

1. **Access the System**
   ```
   URL: http://your-domain.com
   Role: Select "Administrator"
   ```

2. **Default Administrator Account**
   ```
   Username: admin.flood
   Email: admin@floodsystem.gov
   Password: [Initial setup password]
   ```

3. **First Login Steps**
   - Change your password immediately
   - Review user accounts and roles
   - Verify system thresholds and zones
   - Check resource configurations

### System Requirements

- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Screen Resolution**: Minimum 1024x768 (recommended 1920x1080)
- **Internet**: Stable connection for real-time updates

## ✨ Core Features

### 🗺️ Region Management

Complete geographic zone management with interactive mapping:

- **Interactive Zone Editor**: Map-based zone creation and editing
- **GeoJSON Support**: Import/export zone data in standard format
- **Property Configuration**: Set population, assets, and administrative data
- **Real-time Validation**: Automatic zone boundary and property validation
- **Visual Management**: Color-coded zones with clear boundaries

**Key Capabilities:**
- Draw new zones using intuitive drawing tools
- Edit existing zone boundaries and properties
- Import zone data from external GIS systems
- Export current configuration for backup
- Validate zone integrity and completeness

### ⚙️ Threshold Configuration

Comprehensive system threshold and alert rule management:

#### Risk Thresholds
- Configure risk bands (Low, Moderate, High, Severe)
- Set numerical risk value ranges (0.0 - 1.0 scale)
- Visual color coding for each risk level
- Automatic alert generation settings

#### Gauge Thresholds
- Set water level monitoring thresholds
- Configure alert and critical levels for each gauge
- Support for multiple measurement units
- Gauge-specific metadata and descriptions

#### Alert Rules
- Create automated alerting rules
- Multiple trigger types (risk levels, gauge rates, crew activities)
- Configurable notification channels (SMS, Email, Dashboard)
- Cooldown periods to prevent alert fatigue

### 👥 User Management

Complete user administration with role-based access control:

#### User Account Management
- Create, update, and deactivate user accounts
- Assign roles and permissions
- Manage account status (Active, Inactive, Suspended)
- Track login activity and last access

#### Role-Based Access Control
- **Administrator**: Full system access and configuration
- **Planner**: Risk assessment and scenario planning
- **Coordinator**: Live operations and resource deployment
- **Data Analyst**: Analytics, reporting, and data export

#### Security Features
- Password reset functionality
- Zone-based access assignments
- Role permission matrix
- Audit trail support

### 🚚 Resource Management

Three-tier resource management system:

#### Depot Management
- Add and manage depot locations
- Configure service areas and operating hours
- Set capacity limits and contact information
- Track depot status and availability

#### Equipment Management
- Comprehensive equipment inventory
- Multiple equipment types (pumps, vehicles, sandbags)
- Maintenance scheduling and tracking
- Deployment status monitoring

#### Crew Management
- Response crew administration
- Skills and certification tracking
- Team composition and leadership
- Availability and assignment management

## 📖 User Guide

### Daily Operations

#### Morning Check
1. Review system alerts and notifications
2. Check resource availability and status
3. Verify active user sessions
4. Review any pending configuration changes

#### Weekly Tasks
1. Review and update user accounts
2. Check equipment maintenance schedules
3. Validate zone configurations
4. Backup system configurations

#### Monthly Reviews
1. Audit user access and permissions
2. Review alert rule effectiveness
3. Update resource inventories
4. Performance and capacity planning

### Common Workflows

#### Adding a New User
1. Navigate to User Management → Add User
2. Fill in required information (name, email, role)
3. Assign appropriate permissions and zones
4. Set initial account status
5. Send credentials to user

#### Updating Risk Thresholds
1. Go to Threshold Configuration → Risk Thresholds
2. Select the threshold to modify
3. Update risk values and colors
4. Configure automatic alert settings
5. Save and validate changes

#### Managing Equipment
1. Access Resource Management → Equipment
2. Add new equipment or update existing items
3. Set maintenance schedules
4. Configure deployment rules
5. Track usage and status

### Data Management

#### Import Operations
- **Zones**: GeoJSON files with polygon data
- **Users**: CSV files with user information
- **Resources**: JSON files with equipment and crew data

#### Export Operations
- **Complete Export**: All system data and configurations
- **Selective Export**: Specific data types or date ranges
- **Format Options**: JSON, CSV, XML formats available

#### Backup Procedures
- **Automatic Backups**: Scheduled daily backups
- **Manual Backups**: On-demand export functionality
- **Version Control**: Track changes with timestamps
- **Recovery**: Restore from backup files

## 🔐 Security

### Access Control
- **Multi-Factor Authentication**: Optional MFA for admin accounts
- **Session Management**: Automatic timeout and logout
- **IP Restrictions**: Limit access by IP address ranges
- **Audit Logging**: Complete activity tracking

### Data Protection
- **Input Validation**: Comprehensive form validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Output encoding and sanitization
- **CSRF Protection**: Anti-forgery tokens

### Best Practices
- Use strong passwords for admin accounts
- Regularly review user access and permissions
- Keep software and dependencies updated
- Monitor system logs for suspicious activity
- Backup data regularly and test restore procedures

## 📡 API Reference

The Administrator portal exposes a comprehensive REST API for programmatic access:

### Base URL
```
https://your-domain.com/api/admin
```

### Authentication
```
Authorization: Bearer <admin-jwt-token>
```

### Key Endpoints

#### User Management
- `GET /users` - List all users
- `POST /users` - Create new user
- `PUT /users/:id` - Update user
- `DELETE /users/:id` - Delete user

#### Resource Management
- `GET /resources/depots` - List depots
- `POST /resources/depots` - Create depot
- `GET /resources/equipment` - List equipment
- `POST /resources/equipment` - Create equipment

#### Configuration
- `GET /thresholds/risk` - List risk thresholds
- `PUT /thresholds/risk` - Update risk thresholds
- `GET /zones` - Get zone configuration
- `PUT /zones` - Update zone configuration

### API Documentation
Complete API documentation is available at:
- Interactive Swagger UI: `/api-docs`
- Admin API Reference: [Admin API Documentation](../api/admin-endpoints.md)

## 🔧 Troubleshooting

### Common Issues

#### Login Problems
**Problem**: Cannot access administrator portal
**Solutions**:
- Check username and password
- Verify account is active
- Clear browser cache and cookies
- Check system status for maintenance

#### Form Validation Errors
**Problem**: Forms not submitting with validation errors
**Solutions**:
- Review error messages carefully
- Check required field completion
- Verify data format (email, dates, numbers)
- Ensure data meets business rules

#### Zone Editor Issues
**Problem**: Zone map not loading or editing
**Solutions**:
- Check internet connection
- Verify browser supports WebGL
- Clear browser cache
- Try different browser

#### API Connection Issues
**Problem**: Data not saving or loading
**Solutions**:
- Check API server status
- Verify network connectivity
- Check browser console for errors
- Contact system administrator

### Performance Issues

#### Slow Loading
- Check network speed
- Clear browser cache
- Reduce data export size
- Close unused browser tabs

#### Memory Issues
- Refresh browser periodically
- Close unused applications
- Check available system memory

### Getting Help

#### System Resources
- **Documentation**: Complete admin guide and API reference
- **Status Page**: System health and maintenance information
- **Support Portal**: Issue tracking and knowledge base

#### Contact Support
- **Email**: admin-support@floodsystem.gov
- **Phone**: 1-800-FLOOD-HELP (1-800-356-6343)
- **Emergency**: 24/7 emergency support line

#### Training Resources
- **Video Tutorials**: Step-by-step guides for common tasks
- **Webinars**: Live training sessions with Q&A
- **Documentation**: Comprehensive user guides and manuals

---

For additional information or assistance, please refer to the complete [System Documentation](../../README.md) or contact your system administrator.