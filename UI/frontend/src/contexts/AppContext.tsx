import React, { createContext, useContext, useState, useEffect } from 'react';
import type { TimeHorizon } from '../types';

interface AppContextType {
  selectedZone: string | null;
  setSelectedZone: (zone: string | null) => void;
  timeHorizon: TimeHorizon;
  setTimeHorizon: (horizon: TimeHorizon) => void;
  leadTimeDays: number;
  setLeadTimeDays: (d: number) => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [timeHorizon, setTimeHorizon] = useState<TimeHorizon>('1d');
  const [leadTimeDays, setLeadTimeDays] = useState<number>(1);
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    // Apply dark mode class to document
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  const value = {
    selectedZone,
    setSelectedZone,
    timeHorizon,
    setTimeHorizon,
    leadTimeDays,
    setLeadTimeDays,
    darkMode,
    toggleDarkMode,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}