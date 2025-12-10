import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { DataTable, type Column } from '@/components/DataTable';
import { FormDialog, FormField } from '@/components/Forms/FormDialog';
import { Role, SystemUser } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { ROLE_PERMISSIONS } from '@/lib/permissions';
import { Shield, Info, AlertTriangle, Mail, Phone, MapPin } from 'lucide-react';

const roleDescriptions = {
  Administrator: 'Full system access including user management and configuration',
  Planner: 'Risk assessment, scenario planning, and alert management',
  Coordinator: 'Live operations, resource deployment, and crew management',
  'Data Analyst': 'Analytics, reporting, and data export capabilities',
};

export function AdminUsers() {
  const { users, addUser, updateUser, deleteUser, resetPassword, currentUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<SystemUser | null>(null);

  // User Form Fields
  const userFields: FormField[] = [
    {
      key: 'username',
      label: 'Username',
      type: 'text',
      required: true,
      validation: (value) => {
        if (!value.match(/^[a-zA-Z0-9._-]+$/)) {
          return 'Username can only contain letters, numbers, dots, hyphens, and underscores';
        }
        if (value.length < 3) return 'Username must be at least 3 characters';
        return null;
      },
    },
    {
      key: 'email',
      label: 'Email Address',
      type: 'email',
      required: true,
    },
    {
      key: 'firstName',
      label: 'First Name',
      type: 'text',
      required: true,
    },
    {
      key: 'lastName',
      label: 'Last Name',
      type: 'text',
      required: true,
    },
    {
      key: 'role',
      label: 'Role',
      type: 'select',
      required: true,
      options: [
        { value: 'Administrator', label: 'Administrator' },
        { value: 'Planner', label: 'Planner' },
        { value: 'Coordinator', label: 'Coordinator' },
        { value: 'Data Analyst', label: 'Data Analyst' },
      ],
    },
    {
      key: 'department',
      label: 'Department',
      type: 'text',
      required: true,
    },
    {
      key: 'phone',
      label: 'Phone Number',
      type: 'text',
      placeholder: '+1-555-0000',
    },
    {
      key: 'location',
      label: 'Office Location',
      type: 'text',
    },
    {
      key: 'status',
      label: 'Account Status',
      type: 'select',
      required: true,
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'suspended', label: 'Suspended' },
      ],
    },
  ];

  // User Columns for DataTable
  const userColumns: Column<SystemUser>[] = [
    {
      key: 'firstName',
      title: 'Name',
      sortable: true,
      render: (value: string, record: SystemUser) => (
        <div>
          <div className="font-medium">{`${value} ${record.lastName}`}</div>
          <div className="text-sm text-muted-foreground">@{record.username}</div>
        </div>
      ),
    },
    {
      key: 'email',
      title: 'Contact',
      render: (value: string, record: SystemUser) => (
        <div className="space-y-1">
          <div className="flex items-center space-x-1">
            <Mail className="h-3 w-3 text-muted-foreground" />
            <span className="text-sm">{value}</span>
          </div>
          {record.phone && (
            <div className="flex items-center space-x-1">
              <Phone className="h-3 w-3 text-muted-foreground" />
              <span className="text-sm">{record.phone}</span>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'role',
      title: 'Role',
      sortable: true,
      render: (value: Role) => {
        const roleColors = {
          Administrator: 'bg-purple-100 text-purple-800',
          Planner: 'bg-blue-100 text-blue-800',
          Coordinator: 'bg-green-100 text-green-800',
          'Data Analyst': 'bg-orange-100 text-orange-800',
        };
        return (
          <Badge className={roleColors[value]}>
            <Shield className="h-3 w-3 mr-1" />
            {value}
          </Badge>
        );
      },
    },
    {
      key: 'department',
      title: 'Department',
      sortable: true,
    },
    {
      key: 'location',
      title: 'Location',
      sortable: true,
      render: (value: string) => (
        <div className="flex items-center space-x-1">
          <MapPin className="h-3 w-3 text-muted-foreground" />
          <span className="text-sm">{value}</span>
        </div>
      ),
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (value: string) => {
        const statusColors = {
          active: 'bg-green-100 text-green-800',
          inactive: 'bg-gray-100 text-gray-800',
          suspended: 'bg-red-100 text-red-800',
        };
        return (
          <Badge variant="outline" className={statusColors[value as keyof typeof statusColors]}>
            {value}
          </Badge>
        );
      },
    },
    {
      key: 'zones',
      title: 'Assigned Zones',
      render: (value: string[]) => (
        <div className="flex flex-wrap gap-1">
          {value?.length > 0 ? (
            value.map((zone) => (
              <Badge key={zone} variant="outline" className="text-xs">
                {zone}
              </Badge>
            ))
          ) : (
            <span className="text-sm text-muted-foreground">No zones</span>
          )}
        </div>
      ),
    },
    {
      key: 'lastLogin',
      title: 'Last Login',
      sortable: true,
      render: (value: string) => (
        <div className="text-sm">
          {value ? new Date(value).toLocaleDateString() : 'Never'}
        </div>
      ),
    },
  ];

  const handleSaveUser = async (data: Record<string, any>) => {
    try {
      setError(null);
      setLoading(true);

      const payload = {
        username: data.username,
        email: data.email,
        firstName: data.firstName,
        lastName: data.lastName,
        role: data.role,
        department: data.department,
        phone: data.phone,
        location: data.location,
        status: data.status,
        password: data.password,
      };

      if (editingUser) {
        await updateUser(editingUser.id, payload);
      } else {
        await addUser(payload);
      }

      setIsUserDialogOpen(false);
      setEditingUser(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save user';
      setError(errorMessage);
      console.error('Error saving user:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (record: SystemUser) => {
    try {
      setError(null);
      setLoading(true);
      await deleteUser(record.id);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete user';
      setError(errorMessage);
      console.error('Error deleting user:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (user: SystemUser) => {
    try {
      const newPassword = await resetPassword(user.id);
      alert(`Temporary password for ${user.username}: ${newPassword}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reset password';
      setError(errorMessage);
      console.error('Error resetting password:', err);
    }
  };

  const customActions = (record: SystemUser) => (
    <>
      <button
        onClick={() => handleResetPassword(record)}
        className="w-full text-left px-2 py-1 text-sm hover:bg-muted"
      >
        Reset Password
      </button>
    </>
  );

  const activeUsers = users.filter(u => u.status === 'active');
  const inactiveUsers = users.filter(u => u.status === 'inactive');
  const suspendedUsers = users.filter(u => u.status === 'suspended');

  if (currentUser?.role !== 'Administrator') {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Administrator access is required to manage user accounts.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">User Management</h1>

      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
      )}

      <Alert className="mb-6">
        <Info className="h-4 w-4" />
        <AlertDescription>
          Manage system users, roles, and access permissions. Each role has predefined permissions
          that determine what users can access and modify within the flood prediction system.
        </AlertDescription>
      </Alert>

      {/* User Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Total Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{users.length}</div>
            <p className="text-xs text-muted-foreground">Registered accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Active Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{activeUsers.length}</div>
            <p className="text-xs text-muted-foreground">Currently active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Administrators</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {users.filter(u => u.role === 'Administrator').length}
            </div>
            <p className="text-xs text-muted-foreground">System administrators</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Inactive Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{inactiveUsers.length}</div>
            <p className="text-xs text-muted-foreground">Inactive accounts</p>
          </CardContent>
        </Card>
      </div>

      {/* Role Permissions Reference */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Role Permissions Reference</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(roleDescriptions).map(([role, description]) => (
              <div key={role} className="border rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Badge variant="outline">{role}</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-2">{description}</p>
                <div className="space-y-1">
                  {ROLE_PERMISSIONS[role as Role].map((permission) => (
                    <Badge key={permission} variant="secondary" className="text-xs mr-1">
                      {permission.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <DataTable
        data={users}
        columns={userColumns}
        title="System Users"
        description="Manage user accounts and their access levels"
        onAdd={() => {
          setEditingUser(null);
          setIsUserDialogOpen(true);
        }}
        onEdit={(record) => {
          setEditingUser(record);
          setIsUserDialogOpen(true);
        }}
        onDelete={handleDeleteUser}
        rowActions={customActions}
        emptyMessage="No users found"
        loading={loading}
        pageSize={10}
      />

      {/* User Form Dialog */}
      <FormDialog
        open={isUserDialogOpen}
        onOpenChange={setIsUserDialogOpen}
        title={editingUser ? "Edit User" : "Add New User"}
        description={editingUser ? "Update user information and permissions" : "Create a new user account"}
        fields={userFields}
        initialData={editingUser || { status: 'active', role: 'Planner' }}
        onSubmit={handleSaveUser}
      />
    </div>
  );
}
