import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AppContextType, Role, TimeHorizon } from '@/types';

const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [currentRole, setCurrentRole] = useState<Role | null>(() => {
    const saved = localStorage.getItem('flood-prediction-role');
    return saved ? (saved as Role) : null;
  });

  const [selectedZone, setSelectedZone] = useState<string | null>(() => {
    const saved = localStorage.getItem('flood-prediction-selected-zone');
    return saved || null;
  });

  const [timeHorizon, setTimeHorizon] = useState<TimeHorizon>(() => {
    const saved = localStorage.getItem('flood-prediction-time-horizon');
    return (saved as TimeHorizon) || '12h';
  });

  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('flood-prediction-dark-mode');
    return saved ? JSON.parse(saved) : true;
  });

  // Persist changes to localStorage
  useEffect(() => {
    if (currentRole) {
      localStorage.setItem('flood-prediction-role', currentRole);
    } else {
      localStorage.removeItem('flood-prediction-role');
    }
  }, [currentRole]);

  useEffect(() => {
    if (selectedZone) {
      localStorage.setItem('flood-prediction-selected-zone', selectedZone);
    } else {
      localStorage.removeItem('flood-prediction-selected-zone');
    }
  }, [selectedZone]);

  useEffect(() => {
    localStorage.setItem('flood-prediction-time-horizon', timeHorizon);
  }, [timeHorizon]);

  useEffect(() => {
    localStorage.setItem('flood-prediction-dark-mode', JSON.stringify(darkMode));

    // Apply dark mode to document
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const value: AppContextType = {
    currentRole,
    setCurrentRole,
    selectedZone,
    setSelectedZone,
    timeHorizon,
    setTimeHorizon,
    darkMode,
    setDarkMode,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext(): AppContextType {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}