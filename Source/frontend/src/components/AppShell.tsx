import React, { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useAppContext } from '@/contexts/AppContext';
import { useAuth } from '@/contexts/AuthContext';
import { Role } from '@/types';
import {
  MapPin,
  Radio,
  BarChart3,
  LogOut,
  Moon,
  Sun,
  Menu,
  AlertTriangle,
  Layers,
  Users,
  Shield,
  TrendingUp,
  UserCircle2,
} from 'lucide-react';
import { getAdminPath } from '@/lib/routes';

interface AppShellProps {
  children: ReactNode;
}

const navigationConfig = {
  Administrator: [
    { to: getAdminPath('regions'), icon: MapPin, label: 'Regions' },
    { to: getAdminPath('thresholds'), icon: Shield, label: 'Thresholds' },
    { to: getAdminPath('resources'), icon: Layers, label: 'Resources' },
    { to: getAdminPath('users'), icon: Users, label: 'Users' },
  ],
  Planner: [
    { to: '/planner/map', icon: MapPin, label: 'Risk Map' },
    { to: '/planner/scenarios', icon: TrendingUp, label: 'Scenarios' },
    { to: '/planner/alerts', icon: AlertTriangle, label: 'Alerts' },
  ],
  Coordinator: [
    { to: '/coordinator/ops', icon: Radio, label: 'Ops Board' },
    { to: '/coordinator/resources', icon: Layers, label: 'Resources' },
  ],
  'Data Analyst': [
    { to: '/analyst/overview', icon: BarChart3, label: 'Overview' },
    { to: '/analyst/exports', icon: Layers, label: 'Exports' },
  ],
};

const roleColors = {
  Administrator: 'bg-blue-500',
  Planner: 'bg-green-500',
  Coordinator: 'bg-orange-500',
  'Data Analyst': 'bg-purple-500',
};

export function AppShell({ children }: AppShellProps) {
  const { currentRole, darkMode, setDarkMode, setCurrentRole } = useAppContext();
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleRoleSwitch = (role: Role) => {
    setCurrentRole(role);
    // Navigate to the first page of that role
    const roleNavigation = navigationConfig[role];
    if (roleNavigation.length > 0) {
      navigate(roleNavigation[0].to);
    }
  };

  const isAdministrator = currentUser?.role === 'Administrator';

  const navigation = currentRole ? navigationConfig[currentRole] : [];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
        <div className="flex h-14 items-center px-4">
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden mr-2"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Menu className="h-4 w-4" />
          </Button>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-6 w-6 text-orange-500" />
              <h1 className="font-semibold text-lg">Flood Prediction</h1>
            </div>
            {currentRole && (
              <Badge className={`${roleColors[currentRole]} text-white ml-2`}>
                {currentRole}
              </Badge>
            )}
          </div>

          <div className="ml-auto flex items-center space-x-2">
            {/* Dark mode toggle */}
            <Button
              variant="ghost"
              size="sm"
              aria-label="Toggle dark mode"
              onClick={() => setDarkMode(!darkMode)}
            >
              {darkMode ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>

            {currentUser && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <UserCircle2 className="h-4 w-4 mr-2" />
                    {currentUser.firstName}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-60">
                  <DropdownMenuLabel>
                    <div className="text-xs text-muted-foreground">Signed in as</div>
                    <div className="font-medium">{currentUser.firstName} {currentUser.lastName}</div>
                    <div className="text-xs text-muted-foreground">@{currentUser.username}</div>
                    <div className="text-xs text-muted-foreground">Role: {currentUser.role}</div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />

                  {/* Role switching for administrators */}
                  {isAdministrator && (
                    <>
                      <DropdownMenuLabel className="text-xs font-semibold">
                        View as Role:
                      </DropdownMenuLabel>
                      {(['Administrator', 'Planner', 'Coordinator', 'Data Analyst'] as Role[]).map((role) => (
                        <DropdownMenuItem
                          key={role}
                          onClick={() => handleRoleSwitch(role)}
                          className={currentRole === role ? 'bg-accent' : ''}
                        >
                          <div className={`w-3 h-3 rounded-full mr-2 ${roleColors[role]}`} />
                          {role}
                          {currentRole === role && (
                            <span className="ml-auto text-xs">✓</span>
                          )}
                        </DropdownMenuItem>
                      ))}
                      <DropdownMenuSeparator />
                    </>
                  )}

                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`
          fixed md:sticky top-14 left-0 z-40 w-64 h-[calc(100vh-3.5rem)] border-r bg-card/95 backdrop-blur transition-transform
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}>
          <nav className="space-y-2 p-4">
            {navigation.map((item) => {
              const Icon = item.icon;

              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive: linkActive }) => `
                    flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors
                    ${linkActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
