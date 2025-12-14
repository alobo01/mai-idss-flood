import { useState, useEffect } from 'react';

export const useSimulatedTimeline = () => {
  const [lastDataDate, setLastDataDate] = useState<string | null>(null);

  useEffect(() => {
    // Fetch the last raw data date from the API
    const fetchLastDataDate = async () => {
      try {
        const response = await fetch('/api/raw-data/last-date');
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.data?.last_date) {
            setLastDataDate(data.data.last_date);
          }
        }
      } catch (error) {
        console.error('Failed to fetch last data date:', error);
      }
    };

    fetchLastDataDate();

    // Refresh every 10 seconds
    const interval = setInterval(fetchLastDataDate, 10000);

    return () => clearInterval(interval);
  }, []);

  // Format the date for display
  const label = lastDataDate
    ? new Date(lastDataDate).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    : 'Loading...';

  return {
    timestamp: lastDataDate,
    label,
    lastDataDate
  };
};