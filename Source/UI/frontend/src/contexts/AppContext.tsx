import React, { createContext, useContext, useState, useEffect } from 'react';
import type { TimeHorizon, RuleScenario } from '../types';

interface AppContextType {
  selectedZone: string | null;
  setSelectedZone: (zone: string | null) => void;
  timeHorizon: TimeHorizon;
  setTimeHorizon: (horizon: TimeHorizon) => void;
  leadTimeDays: number;
  setLeadTimeDays: (d: number) => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
  scenario: RuleScenario;
  setScenario: (value: RuleScenario) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [leadTimeDays, setLeadTimeDays] = useState<number>(1);
  const [scenario, setScenario] = useState<RuleScenario>('normal');
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

  const timeHorizon: TimeHorizon = leadTimeDays === 2 ? '2d' : leadTimeDays === 3 ? '3d' : '1d';
  const handleSetTimeHorizon = (horizon: TimeHorizon) => {
    const days = horizon === '1d' ? 1 : horizon === '2d' ? 2 : 3;
    setLeadTimeDays(days);
  };

  const value = {
    selectedZone,
    setSelectedZone,
    timeHorizon,
    setTimeHorizon: handleSetTimeHorizon,
    leadTimeDays,
    setLeadTimeDays,
    darkMode,
    toggleDarkMode,
    scenario,
    setScenario,
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
