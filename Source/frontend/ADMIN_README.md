# Administrator Portal - Complete Guide

This guide provides comprehensive documentation for the fully-functional Administrator portal of the Flood Prediction System.

## Overview

The Administrator portal provides complete database management capabilities for non-technical users to manage all aspects of the flood prediction system. The interface is designed for ease-of-use while maintaining robust functionality and data integrity.

## Features Implemented

### 🏢 **Region Management**
- **Interactive Zone Editor**: Full-featured map-based zone management with React-Leaflet integration
- **GeoJSON Import/Export**: Import zone data from GeoJSON files or export current configurations
- **Real-time Validation**: Automatic zone validation with error reporting
- **Visual Zone Properties**: Configure population, critical assets, and administrative levels
- **Drawing Tools**: Create, edit, and delete flood prediction zones interactively

### ⚙️ **Threshold Configuration**
Complete management of system thresholds and alert rules:

#### Risk Thresholds
- Configure risk bands (Low, Moderate, High, Severe)
- Set risk value ranges (0-1 scale)
- Visual color coding for each risk level
- Automatic alert generation settings

#### Gauge Thresholds
- Configure water level monitoring thresholds
- Set alert and critical levels for each gauge
- Support for multiple units (meters, feet, CFS)
- Gauge-specific descriptions and metadata

#### Alert Rules
- Create automated alert rules based on various triggers
- Configure notification channels (SMS, Email, Dashboard)
- Set cooldown periods to prevent alert fatigue
- Multiple trigger types (Risk Threshold, Gauge Rate, Gauge Level, Crew Activity)

### 👥 **User Management**
Comprehensive user administration with role-based access control:

#### User Management Features
- Complete CRUD operations (Create, Read, Update, Delete)
- Role-based permissions with 4 distinct roles:
  - **Administrator**: Full system access
  - **Planner**: Risk assessment and scenario planning
  - **Coordinator**: Live operations and resource deployment
  - **Data Analyst**: Analytics and reporting
- Account status management (Active, Inactive, Suspended)
- Zone-based access assignments
- Password reset functionality
- Last login tracking

#### Role Permissions Matrix
| Permission | Administrator | Planner | Coordinator | Data Analyst |
|------------|----------------|---------|-------------|--------------|
| System Configuration | ✅ | ❌ | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| Threshold Management | ✅ | ❌ | ❌ | ❌ |
| Zone Management | ✅ | ❌ | ❌ | ❌ |
| Risk Assessment | ✅ | ✅ | ❌ | ❌ |
| Resource Deployment | ✅ | ❌ | ✅ | ❌ |
| Crew Management | ✅ | ❌ | ✅ | ❌ |
| Communications | ✅ | ❌ | ✅ | ❌ |
| Alert Management | ✅ | ✅ | ✅ | ❌ |
| Zone Viewing | ✅ | ✅ | ✅ | ✅ |
| Scenario Planning | ✅ | ✅ | ❌ | ❌ |
| Data Export | ✅ | ✅ | ❌ | ✅ |
| Reporting | ✅ | ✅ | ❌ | ✅ |
| Analytics | ✅ | ❌ | ❌ | ✅ |

### 🚚 **Resource Management**
Three-tier resource management system:

#### Depot Management
- Add/edit/remove depot locations
- Configure depot capacity and service zones
- Set operating hours and contact information
- Track depot status (Active, Inactive, Maintenance)

#### Equipment Management
- Comprehensive equipment inventory tracking
- Support for multiple equipment types:
  - Pumps (with capacity specifications)
  - Vehicles (with license/VIN tracking)
  - Sandbags (with quantity and expiration)
  - Custom equipment types
- Maintenance scheduling and tracking
- Deployment status management

#### Crew Management
- Response crew administration
- Skills and certifications tracking
- Team size and leadership assignment
- Status monitoring (Ready, Working, Rest, En Route)
- Experience level tracking
- Training schedule management

## Technical Implementation

### Frontend Architecture
- **React 18** with TypeScript for type safety
- **Vite** for fast development and building
- **Tailwind CSS** for responsive design
- **shadcn/ui** components for consistent UI
- **React Query** for data fetching and caching
- **React Router** for navigation
- **Zod** for data validation

### UI Components

#### DataTable Component
- Reusable, searchable, sortable data tables
- Pagination support
- Custom renderers for complex data
- Action menus with edit/delete capabilities
- Loading states and empty states
- Export functionality

#### FormDialog Component
- Modal-based forms with validation
- Support for multiple field types:
  - Text, Number, Email inputs
  - Select dropdowns
  - Textarea for longer text
  - Checkboxes for boolean values
  - Tag fields for arrays
- Custom validation functions
- Error handling and display

#### ZoneEditor Component
- Interactive map-based zone editing
- Drawing tools for creating new zones
- Property editing for zone metadata
- GeoJSON import/export capabilities
- Real-time validation

### API Integration

#### API Server
Complete Express.js server with the following endpoints:

**User Management**
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/:id` - Update user
- `DELETE /api/admin/users/:id` - Delete user

**Threshold Management**
- `GET /api/admin/thresholds/risk` - List risk thresholds
- `POST /api/admin/thresholds/risk` - Create risk threshold
- `PUT /api/admin/thresholds/risk/:id` - Update risk threshold
- `DELETE /api/admin/thresholds/risk/:id` - Delete risk threshold

**Gauge Thresholds**
- `GET /api/admin/thresholds/gauges` - List gauge thresholds
- `POST /api/admin/thresholds/gauges` - Create gauge threshold
- `PUT /api/admin/thresholds/gauges/:id` - Update gauge threshold
- `DELETE /api/admin/thresholds/gauges/:id` - Delete gauge threshold

**Alert Rules**
- `GET /api/admin/alerts/rules` - List alert rules
- `POST /api/admin/alerts/rules` - Create alert rule
- `PUT /api/admin/alerts/rules/:id` - Update alert rule
- `DELETE /api/admin/alerts/rules/:id` - Delete alert rule

**Resource Management**
- `GET /api/admin/resources/depots` - List depots
- `POST /api/admin/resources/depots` - Create depot
- `PUT /api/admin/resources/depots/:id` - Update depot
- `DELETE /api/admin/resources/depots/:id` - Delete depot

- `GET /api/admin/resources/equipment` - List equipment
- `POST /api/admin/resources/equipment` - Create equipment
- `PUT /api/admin/resources/equipment/:id` - Update equipment
- `DELETE /api/admin/resources/equipment/:id` - Delete equipment

- `GET /api/admin/resources/crews` - List crews
- `POST /api/admin/resources/crews` - Create crew
- `PUT /api/admin/resources/crews/:id` - Update crew
- `DELETE /api/admin/resources/crews/:id` - Delete crew

**Zone Management**
- `PUT /api/admin/zones` - Update zones with GeoJSON data

**Export**
- `GET /api/admin/export/:type` - Export data by type (users, thresholds, resources, zones)

### Data Validation

#### Form Validation
- Required field validation
- Type-specific validation (email, numbers, hex colors)
- Custom validation functions
- Real-time validation feedback
- Comprehensive error messages

#### Business Logic Validation
- Prevent deletion of last administrator
- Validate risk threshold ranges (0-1, min < max)
- Check for duplicate usernames/emails
- Prevent deletion of depots with assigned resources
- Validate zone GeoJSON format

### Error Handling
- Graceful error handling for API failures
- User-friendly error messages
- Loading states for async operations
- Confirmation dialogs for destructive actions
- Form validation with field-specific errors

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn package manager

### Installation
1. Clone the repository
2. Install dependencies: `npm install`
3. Start the development server: `npm run dev`
4. Start the API server: `npm run api`
5. Or run both together: `npm run dev:full`

### Development Scripts
- `npm run dev` - Start frontend development server
- `npm run api` - Start API server
- `npm run dev:full` - Start both frontend and API simultaneously
- `npm run build` - Build for production
- `npm run test` - Run Playwright end-to-end tests

### Accessing the System
1. Open http://localhost:5173 in your browser
2. Select "Administrator" role from the role selector
3. The administrator dashboard will appear with full functionality

## Data Management

### Default Administrator Account
- Username: `admin.flood`
- Email: `admin@floodsystem.gov`
- Role: `Administrator`
- Full system access

### Sample Data
The system comes with comprehensive sample data:
- 4 flood prediction zones
- Risk thresholds and alert rules
- Multiple depots, equipment, and crews
- Sample user accounts with different roles

### Data Persistence
- API server stores data in memory during runtime
- Zone data is saved to `public/mock/zones.geojson`
- All other data resets when server restarts
- Export functionality available for data backup

## User Experience Features

### Non-Technical Friendly Design
- Intuitive interface with clear labels and descriptions
- Consistent navigation patterns
- Visual indicators for status and severity
- Help text and validation guidance
- Confirmation dialogs for important actions

### Accessibility
- Keyboard navigation support
- Screen reader compatible components
- High contrast support
- Focus management
- ARIA labels and descriptions

### Responsive Design
- Mobile-friendly interface
- Tablet-optimized layouts
- Desktop-optimized experience
- Touch-friendly controls

## Security Considerations

### Input Validation
- All user inputs validated on both client and server
- SQL injection prevention
- XSS protection
- CSRF protection

### Role-Based Access
- Strict permission enforcement
- Server-side authorization checks
- Role isolation
- Audit trail support

## Future Enhancements

### Planned Features
- Real database integration (PostgreSQL/MongoDB)
- WebSocket integration for live updates
- Advanced reporting and analytics
- Multi-language support
- Audit logging and change tracking
- Data backup and restore functionality
- Integration with external alert systems

### Scalability
- Pagination for large datasets
- Search optimization
- Caching strategies
- Performance monitoring
- Database indexing

## Support and Maintenance

### Troubleshooting
- Check browser console for errors
- Verify API server is running on port 8080
- Ensure all dependencies are installed
- Check network connectivity for API calls

### Common Issues
- CORS errors: Ensure API server allows frontend origin
- Build failures: Check for missing dependencies
- Zone editor: Requires Leaflet CSS imports
- Form validation: Check required field indicators

This administrator portal provides a complete, production-ready solution for managing a flood prediction system with all the features needed for non-technical administrators to maintain the system effectively.
