import { useEffect, useMemo, useState } from 'react';

import { RISK_TIMELINE as GENERATED_TIMELINE } from './riskTimeline.generated';

const RISK_TIMELINE = GENERATED_TIMELINE && GENERATED_TIMELINE.length > 0
  ? GENERATED_TIMELINE
  : [
      '2025-11-11T12:00:00Z',
      '2025-11-11T13:00:00Z',
      '2025-11-11T14:00:00Z',
      '2025-11-11T15:00:00Z',
      '2025-11-11T16:00:00Z',
      '2025-11-11T17:00:00Z',
      '2025-11-11T18:00:00Z',
    ];

const STEP_MS = 15_000; // one simulated hour every 15 seconds

export interface SimulatedTimeline {
  timestamp: string;
  index: number;
  label: string;
  speedLabel: string;
  nextTickMs: number;
}

export const useSimulatedTimeline = (): SimulatedTimeline => {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % RISK_TIMELINE.length);
    }, STEP_MS);

    return () => clearInterval(timer);
  }, []);

  const timestamp = RISK_TIMELINE[index];

  const label = useMemo(() => {
    const dt = new Date(timestamp);
    return dt.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'UTC',
    }) + ' UTC';
  }, [timestamp]);

  return {
    timestamp,
    index,
    label,
    speedLabel: '1h every 15s',
    nextTickMs: STEP_MS,
  };
};
