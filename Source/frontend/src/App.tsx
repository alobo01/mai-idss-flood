import { Fragment, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@/components/AppShell';
import { useAppContext } from '@/contexts/AppContext';
import { useAuth } from '@/contexts/AuthContext';
import { ADMIN_BASE_PATH, ADMIN_PATH_ALIASES, getAdminPath } from '@/lib/routes';
import { LoginPage } from '@/pages/auth/Login';

// Placeholder page components
import { PlannerMap } from '@/pages/planner/Map';
import { PlannerScenarios } from '@/pages/planner/Scenarios';
import { PlannerAlerts } from '@/pages/planner/Alerts';
import { CoordinatorOps } from '@/pages/coordinator/Ops';
import { CoordinatorResources } from '@/pages/coordinator/Resources';
import { AdminRegions } from '@/pages/admin/Regions';
import { AdminThresholds } from '@/pages/admin/Thresholds';
import { AdminResources } from '@/pages/admin/Resources';
import { AdminUsers } from '@/pages/admin/Users';
import { AnalystOverview } from '@/pages/analyst/Overview';
import { AnalystExports } from '@/pages/analyst/Exports';
import { MapTestPage } from '@/components/MapTestPage';

function App() {
  const { currentRole, setCurrentRole } = useAppContext();
  const { currentUser, isAuthenticated } = useAuth();
  const adminDefaultPath = getAdminPath('regions');

  useEffect(() => {
    if (currentUser?.role && currentUser.role !== currentRole) {
      setCurrentRole(currentUser.role);
    } else if (!currentUser && currentRole) {
      setCurrentRole(null);
    }
  }, [currentRole, currentUser, setCurrentRole]);

  if (!isAuthenticated || !currentUser) {
    return <LoginPage />;
  }

  if (!currentRole) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground">
        Preparing your workspace...
      </div>
    );
  }

  return (
    <AppShell>
      <Routes>
        {/* Default redirect based on role */}
        <Route path="/" element={
          <Navigate
            to={
              currentRole === 'Administrator' ? adminDefaultPath :
              currentRole === 'Data Analyst' ? '/analyst/overview' :
              currentRole === 'Coordinator' ? '/coordinator/ops' :
              '/planner/map'
            }
            replace
          />
        } />

        {ADMIN_PATH_ALIASES.map((basePath) => (
          <Route
            key={`${basePath}-root`}
            path={basePath}
            element={<Navigate to={adminDefaultPath} replace />}
          />
        ))}

        {/* Planner Routes */}
        <Route path="/planner/map" element={<PlannerMap />} />
        <Route path="/planner/scenarios" element={<PlannerScenarios />} />
        <Route path="/planner/alerts" element={<PlannerAlerts />} />

        {/* Coordinator Routes */}
        <Route path="/coordinator/ops" element={<CoordinatorOps />} />
        <Route path="/coordinator/resources" element={<CoordinatorResources />} />

        {/* Administrator Routes (support legacy /admin paths) */}
        {ADMIN_PATH_ALIASES.map((basePath) => (
          <Fragment key={basePath}>
            <Route path={`${basePath}/regions`} element={<AdminRegions />} />
            <Route path={`${basePath}/thresholds`} element={<AdminThresholds />} />
            <Route path={`${basePath}/resources`} element={<AdminResources />} />
            <Route path={`${basePath}/users`} element={<AdminUsers />} />
          </Fragment>
        ))}
        
        {/* Data Analyst Routes */}
        <Route path="/analyst/overview" element={<AnalystOverview />} />
        <Route path="/analyst/exports" element={<AnalystExports />} />

        {/* Test Route */}
        <Route path="/test/map" element={<MapTestPage />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

export default App;
