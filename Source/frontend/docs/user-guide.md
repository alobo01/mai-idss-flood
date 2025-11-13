# 📖 User Guide

Complete user manual for the Flood Prediction Frontend application covering all roles and functionality.

## Table of Contents

- [Getting Started](#getting-started)
- [Role Overview](#role-overview)
- [Administrator Role](#administrator-role)
- [Planner Role](#planner-role)
- [Coordinator Role](#coordinator-role)
- [Data Analyst Role](#data-analyst-role)
- [Common Features](#common-features)
- [Mobile Usage](#mobile-usage)
- [Troubleshooting](#troubleshooting)

## Getting Started

### System Requirements

- **Desktop**: Modern browser (Chrome, Firefox, Safari, Edge)
- **Mobile**: iOS 12+ or Android 8+
- **Network**: Stable internet connection
- **Screen Resolution**: Minimum 320px width, recommended 1920x1080

### First Login

1. Open the application URL in your browser
2. You'll see the role selection screen
3. Click **Select [Role Name]** to choose your role
4. The system will remember your role preference

### Navigation Basics

- **Header**: Contains application title, role badge, dark mode toggle, and role switcher
- **Sidebar**: Role-specific navigation menu (hidden on mobile)
- **Main Content**: Current page content
- **Mobile Menu**: Hamburger icon to open sidebar on mobile devices

## Role Overview

### 🛡️ Administrator
**Purpose**: System configuration and management
**Access**: Regions, thresholds, resources, users, system settings

### 📍 Planner
**Purpose**: Risk assessment and scenario planning
**Access**: Risk maps, alerts, scenarios, planning tools

### 📻 Coordinator
**Purpose**: Live operations management
**Access**: Operations board, resources, communications, alerts

### 📊 Data Analyst
**Purpose**: Data analysis and reporting
**Access**: Analytics, exports, data visualization

## Administrator Role

### Dashboard Overview
The Administrator view provides system-wide configuration capabilities:

- **Regions**: Geographic zone management
- **Thresholds**: Alert level configurations
- **Resources**: Equipment and personnel management
- **Users**: Role and access control management

### Regions Management

**Purpose**: Define and manage geographic flood risk zones

**Features**:
- Zone creation and editing
- Population and asset assignment
- Geographic boundary definition
- Zone hierarchy management

**Workflow**:
1. Navigate to **Regions** from sidebar
2. View existing zones in list or map format
3. Click **Add Zone** to create new regions
4. Define zone boundaries using map tools
5. Assign population counts and critical assets
6. Save zone configuration

**Common Operations**:
- **Edit Zone**: Modify existing zone boundaries or properties
- **Delete Zone**: Remove zones (requires confirmation)
- **Import Zones**: Upload GeoJSON files for bulk creation
- **Export Zones**: Download zone data for backup

### Threshold Configuration

**Purpose**: Set alert levels and risk thresholds

**Features**:
- Risk level definitions (Low, Medium, High, Critical)
- Custom threshold values per zone
- Alert trigger conditions
- Notification preferences

**Workflow**:
1. Navigate to **Thresholds** from sidebar
2. Select zone or set global thresholds
3. Configure risk levels:
   - **Low Risk**: 0.0 - 0.25 probability
   - **Medium Risk**: 0.25 - 0.50 probability
   - **High Risk**: 0.50 - 0.75 probability
   - **Critical Risk**: 0.75 - 1.00 probability
4. Set alert triggers and notifications
5. Save threshold configuration

### Resource Catalog

**Purpose**: Manage emergency resources and equipment

**Features**:
- Resource inventory management
- Depot location management
- Crew assignment and scheduling
- Maintenance tracking

**Resource Types**:
- **Pumps**: Various capacity water pumps
- **Barriers**: Flood barriers and sandbags
- **Vehicles**: Emergency response vehicles
- **Equipment**: Communication and safety equipment

**Workflow**:
1. Navigate to **Resources** from sidebar
2. View current resource inventory
3. Click **Add Resource** to register new equipment
4. Assign to depot and crew
5. Set maintenance schedule
6. Save resource details

### User Management

**Purpose**: Manage system users and access controls

**Features**:
- User account creation and management
- Role assignment and permissions
- Access control configuration
- User activity monitoring

**Workflow**:
1. Navigate to **Users** from sidebar
2. View existing user list
3. Click **Add User** to create new accounts
4. Assign role and permissions
5. Set user preferences and notifications
6. Save user configuration

## Planner Role

### Dashboard Overview
The Planner view focuses on risk assessment and planning:

- **Risk Map**: Interactive flood risk visualization
- **Scenarios**: What-if analysis and planning tools
- **Alerts**: Alert management and response planning

### Risk Map Navigation

**Purpose**: Visualize current and predicted flood risks

**Features**:
- Interactive map with risk overlays
- Zone-based risk assessment
- Time horizon selection (0-24 hours)
- Layer controls for different data views

**Map Controls**:
- **Zoom**: Scroll wheel or zoom buttons
- **Pan**: Click and drag to move map
- **Layers**: Toggle risk zones, assets, resources
- **Time Slider**: Select prediction time horizon

**Workflow**:
1. Navigate to **Risk Map** from sidebar
2. View current risk levels by color (green = low, red = critical)
3. Use time slider to see predicted changes
4. Click zones for detailed risk information
5. Toggle layers to show/hide different data types
6. Export map view for reports

**Risk Levels**:
- 🟢 **Green**: Low risk (0.0 - 0.25)
- 🟡 **Yellow**: Medium risk (0.25 - 0.50)
- 🟠 **Orange**: High risk (0.50 - 0.75)
- 🔴 **Red**: Critical risk (0.75 - 1.00)

### Scenario Workbench

**Purpose**: Create and analyze flood response scenarios

**Features**:
- What-if scenario modeling
- Resource allocation simulation
- Impact assessment tools
- Scenario comparison

**Workflow**:
1. Navigate to **Scenarios** from sidebar
2. Click **Create Scenario** to start new analysis
3. Configure scenario parameters:
   - Rainfall intensity
   - Time duration
   - Resource availability
4. Run simulation
5. Analyze results and impacts
6. Save or export scenario

**Scenario Types**:
- **Rainfall Scenario**: Variable precipitation events
- **Levee Failure**: Infrastructure breach scenarios
- **Resource Constraint**: Limited resource scenarios
- **Evacuation Planning**: Population movement scenarios

### Alerts Timeline

**Purpose**: Monitor and manage flood alerts

**Features**:
- Chronological alert display
- Alert severity filtering
- Alert acknowledgment
- Response tracking

**Alert Types**:
- **System Alerts**: Automated risk threshold breaches
- **Crew Alerts**: Field-reported observations
- **Weather Alerts**: External weather service warnings

**Workflow**:
1. Navigate to **Alerts** from sidebar
2. View alerts by time and severity
3. Click alert for detailed information
4. Acknowledge alerts requiring action
5. Track response status and updates
6. Generate alert reports

## Coordinator Role

### Dashboard Overview
The Coordinator view manages live operations:

- **Ops Board**: Real-time operations management
- **Resources**: Live resource tracking and allocation
- **Communications**: Crew communication management

### Live Operations Board

**Purpose**: Real-time operational management

**Features**:
- Live status updates
- Resource tracking
- Incident management
- Team coordination

**Board Sections**:
- **Active Incidents**: Current flood events
- **Resource Status**: Equipment and crew locations
- **Team Assignment**: Current crew deployments
- **Operational Metrics**: Key performance indicators

**Workflow**:
1. Navigate to **Ops Board** from sidebar
2. Monitor live incident feeds
3. Track resource deployments and availability
4. Coordinate team assignments
5. Update operational status
6. Generate situation reports

**Real-time Updates**:
- **Incident Creation**: New flood reports
- **Resource Movement**: Equipment deployments
- **Status Changes**: Crew availability updates
- **Alert Acknowledgment**: Response confirmations

### Resource Allocation

**Purpose**: Deploy and manage emergency resources

**Features**:
- Live resource tracking
- Deployment planning
- Availability monitoring
- Performance metrics

**Workflow**:
1. Navigate to **Resources** from sidebar
2. View current resource deployments
3. Check availability for new deployments
4. Assign resources to incidents
5. Monitor deployment progress
6. Track resource utilization

**Resource States**:
- **Available**: Ready for deployment
- **Deployed**: Currently assigned to incident
- **Maintenance**: Under repair or service
- **Unavailable**: Out of service

### Communications Panel

**Purpose**: Manage crew communications and coordination

**Features**:
- Real-time messaging
- Channel management
- Communication history
- Emergency broadcasting

**Workflow**:
1. Navigate to **Communications** from sidebar
2. Select communication channel
3. View message history
4. Send messages to teams
5. Monitor communication flow
6. Export communication logs

**Channel Types**:
- **All Teams**: System-wide announcements
- **Zone Specific**: Geographic-based teams
- **Function Specific**: Role-based communications
- **Emergency**: Critical incident communications

## Data Analyst Role

### Dashboard Overview
The Data Analyst view provides analytical and reporting tools:

- **Overview**: Analytical map and data visualization
- **Exports**: Data export and reporting tools

### Analytical Map

**Purpose**: Advanced data visualization and analysis

**Features**:
- Multi-layer data visualization
- Statistical analysis tools
- Custom data overlays
- Interactive filtering

**Workflow**:
1. Navigate to **Overview** from sidebar
2. Configure analytical layers
3. Apply filters and time ranges
4. Analyze statistical data
5. Generate insights and reports
6. Export analytical results

**Analytical Tools**:
- **Risk Trends**: Historical risk pattern analysis
- **Damage Assessment**: Infrastructure impact analysis
- **Resource Efficiency**: Deployment effectiveness
- **Predictive Models**: Risk prediction accuracy

### Export Functionality

**Purpose**: Generate reports and export data

**Features**:
- Multiple export formats
- Custom report generation
- Scheduled reports
- Data validation

**Export Formats**:
- **PDF**: Executive summary reports
- **CSV**: Raw data for analysis
- **GeoJSON**: Geographic data
- **Images**: Map snapshots and visualizations

**Workflow**:
1. Navigate to **Exports** from sidebar
2. Select export type and format
3. Configure export parameters:
   - Date range
   - Data filters
   - Report template
4. Generate preview
5. Download or schedule export
6. Track export history

**Report Types**:
- **Daily Summary**: Operational overview
- **Incident Report**: Specific event analysis
- **Trend Analysis**: Historical pattern analysis
- **Resource Report**: Deployment and utilization

## Common Features

### Dark Mode

**Purpose**: Reduce eye strain and improve visibility

**Usage**:
1. Click moon/sun icon in header
2. Toggle between light and dark themes
3. Preference is automatically saved

### Role Switching

**Purpose**: Quickly change between user roles

**Usage**:
1. Click current role badge in header
2. Select new role from dropdown
3. System navigates to new role dashboard

### Responsive Design

**Mobile Features**:
- Collapsible sidebar navigation
- Touch-friendly controls
- Optimized map interactions
- Simplified data tables

**Tablet Features**:
- Adaptive layout changes
- Enhanced touch interactions
- Split-screen capabilities

## Mobile Usage

### Navigation

- **Menu Button**: Hamburger icon opens sidebar
- **Touch Gestures**: Swipe to navigate, pinch to zoom maps
- **Back Button**: Use browser/device back navigation

### Map Interaction

- **Single Tap**: Select map features
- **Double Tap**: Zoom in
- **Pinch**: Zoom in/out
- **Drag**: Pan map view

### Form Input

- **Dropdowns**: Native mobile select controls
- **Date/Time**: Mobile-optimized pickers
- **Number Input**: Mobile numeric keyboards

## Troubleshooting

### Common Issues

**Page Not Loading**:
- Check internet connection
- Clear browser cache
- Try refreshing the page
- Verify correct URL

**Map Not Displaying**:
- Check browser compatibility
- Enable location services if required
- Try different browser
- Check console for errors

**Data Not Updating**:
- Check API connection status
- Refresh the page
- Check network connectivity
- Contact system administrator

**Mobile Issues**:
- Ensure updated browser version
- Check device storage space
- Clear browser data
- Try portrait/landscape orientation

### Performance Tips

- Use modern browsers (Chrome, Firefox, Safari)
- Keep browser updated to latest version
- Close unnecessary tabs
- Ensure stable internet connection
- Regularly clear browser cache

### Getting Help

1. **Check Documentation**: Review relevant sections
2. **Contact Administrator**: For system issues
3. **User Training**: Schedule training sessions
4. **Feedback**: Provide improvement suggestions

---

For additional support or questions, contact your system administrator or refer to the [technical documentation](../README.md).