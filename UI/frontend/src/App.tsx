import React, { useState } from 'react';
import { PlannerMap } from './pages/planner/Map';
import { ResourcesPage } from './pages/planner/Resources';
import { AdministratorPage } from './pages/administrator/Administrator';
import { AppProvider } from './contexts/AppContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Button } from './components/ui/button';
import { Map, Package, Settings, UserCheck, Shield, Calendar } from 'lucide-react';
import './index.css';

type UserRole = 'planner' | 'administrator';

function App() {
  const [userRole, setUserRole] = useState<UserRole>('planner');
  const [selectedDate, setSelectedDate] = useState<string>('');

  return (
    <AppProvider>
      <div className="min-h-screen bg-background">
        {/* Skip link for keyboard users */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <div className="container mx-auto p-6">
          <header className="flex flex-col gap-4 mb-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center space-x-4">
              <img src="/images/logo.png" alt="IDSS logo" className="h-10 w-10 rounded" />
              <h1 className="text-lg font-semibold">IDSS Flood Risk</h1>
            </div>
            <div className="flex-1 flex justify-center">
              <div className="flex flex-col items-center gap-1">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Historical anchor
                </span>
                <div className="flex items-center gap-2">
                  <div className="relative group">
                    <input
                      id="global-date-picker"
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      max={new Date().toISOString().split('T')[0]}
                      className={`px-3 py-2 rounded-lg border transition-all duration-200 text-sm ${
                        selectedDate
                          ? 'bg-blue-600 text-white border-blue-600 shadow-lg'
                          : 'bg-white/90 backdrop-blur-sm text-gray-700 border-gray-300 shadow-md hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200'
                      }`}
                      placeholder="Select date"
                      aria-label="Select anchor date for forecasts"
                    />
                    {selectedDate && (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          setSelectedDate('');
                        }}
                        className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600 transition-colors shadow-md"
                        title="Clear anchor date"
                      >
                        ×
                      </button>
                    )}
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">
                  {selectedDate
                    ? `As of ${new Date(selectedDate).toLocaleDateString()}`
                    : 'Using latest available data'}
                </span>
              </div>
            </div>
            <div className="flex flex-col items-end space-y-2">
              <span className="text-sm font-medium text-muted-foreground">Select Role</span>
              <div className="flex rounded-lg border bg-background p-1 shadow-sm">
                <Button
                  variant={userRole === 'planner' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setUserRole('planner')}
                  className="flex items-center space-x-2 transition-all duration-200"
                >
                  <UserCheck className="h-4 w-4" />
                  <span>Planner</span>
                </Button>
                <Button
                  variant={userRole === 'administrator' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setUserRole('administrator')}
                  className="flex items-center space-x-2 transition-all duration-200"
                >
                  <Shield className="h-4 w-4" />
                  <span>Administrator</span>
                </Button>
              </div>
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
                  <PlannerMap selectedDate={selectedDate} />
                </TabsContent>

                <TabsContent value="resources">
                  <ResourcesPage selectedDate={selectedDate} />
                </TabsContent>
              </Tabs>
            ) : (
              <AdministratorPage selectedDate={selectedDate} />
            )}
          </main>
        </div>
      </div>
    </AppProvider>
  );
}

export default App;
