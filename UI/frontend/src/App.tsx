import React from 'react';
import { PlannerMap } from './pages/planner/Map';
import { AppProvider } from './contexts/AppContext';
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
          <main id="main-content">
            <PlannerMap />
          </main>
        </div>
      </div>
    </AppProvider>
  );
}

export default App;