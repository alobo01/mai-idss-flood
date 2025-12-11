import React from 'react';
import { PlannerMap } from './pages/planner/Map';
import { ResourcesPage } from './pages/planner/Resources';
import { AppProvider } from './contexts/AppContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Map, Package } from 'lucide-react';
import './index.css';

function App() {
  return (
    <AppProvider>
      <div className="min-h-screen bg-background">
        {/* Skip link for keyboard users */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <div className="container mx-auto p-6">
          <header className="flex items-center space-x-4 mb-4">
            <img src="/images/logo.png" alt="IDSS logo" className="h-10 w-10 rounded" />
            <h1 className="text-lg font-semibold">IDSS Flood Risk</h1>
          </header>
          <main id="main-content">
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
          </main>
        </div>
      </div>
    </AppProvider>
  );
}

export default App;