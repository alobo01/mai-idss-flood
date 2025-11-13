import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@/components/AppShell';
import { RoleSelector } from '@/components/RoleSelector';
import { useAppContext } from '@/contexts/AppContext';

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
  const { currentRole } = useAppContext();

  if (!currentRole) {
    return <RoleSelector />;
  }

  return (
    <AppShell>
      <Routes>
        {/* Default redirect based on role */}
        <Route path="/" element={
          <Navigate
            to={
              currentRole === 'Administrator' ? '/admin/regions' :
              currentRole === 'Data Analyst' ? '/analyst/overview' :
              currentRole === 'Coordinator' ? '/coordinator/ops' :
              '/planner/map'
            }
            replace
          />
        } />

        {/* Planner Routes */}
        <Route path="/planner/map" element={<PlannerMap />} />
        <Route path="/planner/scenarios" element={<PlannerScenarios />} />
        <Route path="/planner/alerts" element={<PlannerAlerts />} />

        {/* Coordinator Routes */}
        <Route path="/coordinator/ops" element={<CoordinatorOps />} />
        <Route path="/coordinator/resources" element={<CoordinatorResources />} />

        {/* Administrator Routes */}
        <Route path="/admin/regions" element={<AdminRegions />} />
        <Route path="/admin/thresholds" element={<AdminThresholds />} />
        <Route path="/admin/resources" element={<AdminResources />} />
        <Route path="/admin/users" element={<AdminUsers />} />
        
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