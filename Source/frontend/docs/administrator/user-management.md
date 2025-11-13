# User Management Guide

This comprehensive guide covers all aspects of user management in the Flood Prediction System Administrator Portal.

## 📋 Overview

User Management allows administrators to create, configure, and manage all user accounts in the system. It provides role-based access control, zone-based permissions, and comprehensive account management features.

## 🎭 User Roles and Permissions

The system supports four distinct user roles, each with specific permissions and capabilities:

### Administrator
**Full system access and configuration capabilities**

**Permissions:**
- system_config - System configuration and settings
- user_management - User account management
- threshold_management - Risk threshold and alert rule configuration
- zone_management - Geographic zone configuration
- risk_assessment - View and analyze risk data
- resource_deployment - Manage resource deployment

**Capabilities:**
- Create and manage all user accounts
- Configure system thresholds and alerts
- Manage geographic zones
- Access all system features
- Export and import system data

### Planner
**Risk assessment and scenario planning**

**Permissions:**
- risk_assessment - Comprehensive risk analysis
- scenario_planning - Create and manage response scenarios
- alert_management - Monitor and manage alerts
- zone_viewing - View zone information
- reporting - Generate reports and analysis

**Capabilities:**
- Analyze flood risk and trends
- Create emergency response scenarios
- Monitor system alerts
- View zone-specific information
- Generate analytical reports

### Coordinator
**Live operations and resource deployment**

**Permissions:**
- resource_deployment - Deploy and manage resources
- crew_management - Manage response crews
- communications - Send and receive communications
- alert_management - Handle active alerts
- zone_viewing - View zone information

**Capabilities:**
- Deploy equipment and crews
- Manage ongoing operations
- Coordinate emergency responses
- Send emergency communications
- Track resource status

### Data Analyst
**Analytics, reporting, and data export**

**Permissions:**
- data_export - Export system data
- reporting - Create detailed reports
- analytics - Perform data analysis
- zone_viewing - View zone information

**Capabilities:**
- Export system data for analysis
- Create detailed reports
- Analyze trends and patterns
- Generate visualizations
- Support data-driven decisions

## 👥 User Account Management

### Creating New Users

#### Step 1: Access User Management
1. Log in as Administrator
2. Navigate to **Users** from the main menu
3. Click **Add New User** button

#### Step 2: Fill in User Information
**Required Fields:**
- **Username**: Unique identifier for login (3+ characters)
- **Email Address**: Valid email for notifications
- **First Name**: User's given name
- **Last Name**: User's family name
- **Role**: User's system role
- **Department**: Organizational department
- **Account Status**: Active, Inactive, or Suspended

**Optional Fields:**
- **Phone Number**: Contact phone
- **Office Location**: Physical office location
- **Assigned Zones**: Geographic zones the user can access

#### Step 3: Configure Permissions
- **Role Selection**: Choose from Administrator, Planner, Coordinator, or Data Analyst
- **Zone Assignment**: Select zones the user can access (applicable for non-Administrators)
- **Automatic Permissions**: System assigns permissions based on role

#### Step 4: Review and Create
- Verify all information is correct
- Check for validation errors
- Click **Create User** to finalize

**Example User Creation:**
```json
{
  "username": "coordinator.davis",
  "email": "davis.coord@agency.gov",
  "firstName": "Robert",
  "lastName": "Davis",
  "role": "Coordinator",
  "department": "Operations",
  "phone": "+1-555-0150",
  "location": "Field Operations Center",
  "status": "active",
  "zones": ["Z-CHARLIE", "Z-ECHO"]
}
```

### Updating Existing Users

#### Editing User Information
1. Go to User Management
2. Find the user using search or browse
3. Click the **Edit** action in the user's row
4. Modify the required fields
5. Click **Save Changes**

#### Changing User Roles
- Changing a user's role automatically updates their permissions
- Zone assignments may need adjustment based on new role
- System logs all role changes for audit purposes

#### Managing Account Status
- **Active**: User can log in and access permitted features
- **Inactive**: User cannot log in, account preserved
- **Suspended**: User immediately logged out, cannot log in

### Deleting Users

#### Safety Measures
- System prevents deletion of the last administrator
- Users with active assignments cannot be immediately deleted
- Data associated with deleted users is archived

#### Deletion Process
1. Select the user to delete
2. Confirm deletion in the dialog
3. Review any active assignments or dependencies
4. Confirm final deletion

## 🔐 Security and Access Control

### Zone-Based Access Control

Users (except Administrators) are restricted to specific geographic zones:

- **Zone Assignment**: Administrators assign zones to users during creation
- **Access Restrictions**: Users can only view and interact with their assigned zones
- **Data Filtering**: System automatically filters data based on user zones
- **Cross-Zone Operations**: Only available to users with multiple zone assignments

### Password Management

#### Password Reset
1. Find the user in User Management
2. Click the **Reset Password** action
3. System generates password reset link
4. Link sent to user's email address
5. User has 24 hours to complete reset

#### Password Policies
- **Minimum Length**: 12 characters
- **Complexity**: Mixed case, numbers, symbols required
- **History**: Cannot reuse last 5 passwords
- **Expiration**: 90-day rotation policy
- **Lockout**: 5 failed attempts, 15-minute lockout

### Session Management

#### Session Configuration
- **Idle Timeout**: 30 minutes of inactivity
- **Maximum Session**: 8 hours total
- **Concurrent Sessions**: Maximum 3 per user
- **Remember Me**: 7 days if enabled

#### Session Monitoring
- Track active user sessions
- Force logout for security reasons
- Monitor suspicious login patterns
- Geographic location tracking

## 📊 User Analytics and Reporting

### User Activity Monitoring

#### Login Tracking
- Last login date and time
- Login frequency and patterns
- Failed login attempts
- Geographic location of logins

#### Feature Usage
- Most frequently used features
- Time spent in different areas
- Zone access patterns
- Report generation statistics

### Audit Trail

#### Logged Actions
- User account creation and modification
- Role changes and permission updates
- Password resets and changes
- Zone assignment modifications

#### Audit Reports
- Generate user activity reports
- Export audit logs for compliance
- Filter by date range or user
- Search specific actions or events

## 🚨 Common User Management Scenarios

### New Employee Onboarding

#### Standard Process
1. **Create User Account**
   - Assign appropriate role based on job function
   - Set up initial password reset
   - Assign relevant zones

2. **Training Setup**
   - Create temporary training account if needed
   - Assign limited permissions during training
   - Schedule training sessions

3. **Production Access**
   - Promote to full production account
   - Remove training account
   - Verify all permissions are correct

### Role Changes and Promotions

#### Promotion Process
1. **Assess New Responsibilities**
   - Determine new role requirements
   - Identify additional zone access needs
   - Review permission requirements

2. **Update User Account**
   - Change role in user profile
   - Update zone assignments as needed
   - Verify new permissions

3. **Training and Support**
   - Provide training for new role features
   - Update documentation access
   - Monitor usage during transition

### Departing Employees

#### Offboarding Process
1. **Immediate Actions**
   - Change account status to "Suspended"
   - Revoke all active sessions
   - Update critical contact information

2. **Data Handoff**
   - Transfer assigned resources
   - Reassign active responsibilities
   - Archive user's work and data

3. **Account Finalization**
   - Change status to "Inactive" after transition
   - Export user's data for records
   - Consider account deletion after retention period

### Temporary Access

#### Contract Workers and Consultants
1. **Create Temporary Account**
   - Set appropriate expiration date
   - Limit permissions to essential functions
   - Assign specific zones only

2. **Monitor Usage**
   - Regular access reviews
   - Feature usage monitoring
   - Compliance verification

3. **Account Expiration**
   - Automatic expiration notices
   - Data export before closure
   - Smooth transition if needed

## 🔧 Advanced User Management

### Bulk User Operations

#### Bulk Import
```csv
username,firstName,lastName,email,role,department,phone
contractor.john,John Doe,john@contractor.com,Planner,Planning,+1-555-0100
contractor.jane,Jane Smith,jane@contractor.com,Coordinator,Operations,+1-555-0101
```

#### Bulk Updates
- Mass role changes
- Zone assignment updates
- Department transfers
- Status modifications

### User Groups and Teams

#### Creating Groups
- Group similar users for easier management
- Apply common permissions or settings
- Simplify bulk operations
- Enhance reporting capabilities

#### Group Management
- Create and manage user groups
- Assign users to multiple groups
- Group-based permissions
- Dynamic group membership

## 📞 Support and Troubleshooting

### Common Issues

#### Login Problems
**User cannot log in**
- Verify account status is "Active"
- Check for account lockout
- Verify correct username
- Reset password if necessary

#### Permission Issues
**User cannot access expected features**
- Verify role is correct
- Check zone assignments
- Review permission matrix
- Look for permission overrides

#### Zone Access Problems
**User cannot see certain zones**
- Verify zone assignments
- Check zone visibility settings
- Review role-based zone access
- Confirm zone data exists

### Getting Help

#### Documentation Resources
- Complete User Guide: [Administrator Guide](README.md)
- Role Reference: [Role Management](../roles.md)
- Security Guide: [Security Documentation](security.md)

#### Support Channels
- **Technical Support**: admin-support@floodsystem.gov
- **Security Issues**: security@floodsystem.gov
- **Training Requests**: training@floodsystem.gov
- **Emergency Support**: 1-800-FLOOD-HELP

#### Training Resources
- Video Tutorials: [Training Portal](https://training.floodsystem.gov)
- Live Training: Monthly admin workshops
- Knowledge Base: [Support Portal](https://support.floodsystem.gov)

## 📈 Best Practices

### Security Best Practices
- Regular password audits and enforcement
- Monitor login patterns for anomalies
- Implement least-privilege access principles
- Regular access reviews and cleanups

### Operational Best Practices
- Document all role assignments and justifications
- Maintain current contact information
- Regular training for all users
- Backup user configuration data

### Compliance Best Practices
- Maintain complete audit trails
- Regular access control reviews
- Document all permission changes
- Follow data retention policies

---

For additional information about user management or other administrator functions, please refer to the complete [Administrator Documentation](README.md).