import React, { useState } from 'react';
import { PlannerMap } from './pages/planner/Map';
import { ResourcesPage } from './pages/planner/Resources';
import { AdministratorPage } from './pages/administrator/Administrator';
import { AppProvider } from './contexts/AppContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Map, Package, Settings } from 'lucide-react';
import './index.css';

type UserRole = 'planner' | 'administrator';

function App() {
  const [userRole, setUserRole] = useState<UserRole>('planner');

  return (
    <AppProvider>
      <div className="min-h-screen bg-background">
        {/* Skip link for keyboard users */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <div className="container mx-auto p-6">
          <header className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <img src="/images/logo.png" alt="IDSS logo" className="h-10 w-10 rounded" />
              <h1 className="text-lg font-semibold">IDSS Flood Risk</h1>
            </div>
            <div className="flex items-center space-x-3">
              <label htmlFor="role-select" className="text-sm font-medium">
                Role:
              </label>
              <select
                id="role-select"
                value={userRole}
                onChange={(e) => setUserRole(e.target.value as UserRole)}
                className="border rounded px-3 py-1 text-sm bg-white"
              >
                <option value="planner">Planner</option>
                <option value="administrator">Administrator</option>
              </select>
            </div>
          </header>
          <main id="main-content">
            {userRole === 'planner' ? (
              <Tabs defaultValue="map" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="map" className="flex items-center space-x-2">
                    <Map className="h-4 w-4" />
                    <span>Risk Map</span>
                  </TabsTrigger>
                  <TabsTrigger value="resources" className="flex items-center space-x-2">
                    <Package className="h-4 w-4" />
                    <span>Resources</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="map">
                  <PlannerMap />
                </TabsContent>

                <TabsContent value="resources">
                  <ResourcesPage />
                </TabsContent>
              </Tabs>
            ) : (
              <AdministratorPage />
            )}
          </main>
        </div>
      </div>
    </AppProvider>
  );
}

export default App;