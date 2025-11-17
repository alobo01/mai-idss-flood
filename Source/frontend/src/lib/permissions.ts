import { Role } from '@/types';

export const ROLE_PERMISSIONS: Record<Role, string[]> = {
  Administrator: [
    'system_config',
    'user_management',
    'threshold_management',
    'zone_management',
    'risk_assessment',
    'resource_deployment',
  ],
  Planner: [
    'risk_assessment',
    'scenario_planning',
    'alert_management',
    'zone_viewing',
    'reporting',
  ],
  Coordinator: [
    'resource_deployment',
    'crew_management',
    'communications',
    'alert_management',
    'zone_viewing',
  ],
  'Data Analyst': ['data_export', 'reporting', 'analytics', 'zone_viewing'],
};

export const getRolePermissions = (role: Role) => ROLE_PERMISSIONS[role] || [];
