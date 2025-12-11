import { useState, useEffect } from 'react';

export const useSimulatedTimeline = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Mock timeline dates from 2019 flood event
  const timelineDates = [
    '2019-06-01T12:00:00Z',
    '2019-06-02T12:00:00Z',
    '2019-06-03T12:00:00Z',
    '2019-06-04T12:00:00Z',
    '2019-06-05T12:00:00Z',
    '2019-06-06T12:00:00Z',
    '2019-06-07T12:00:00Z',
    '2019-06-08T12:00:00Z',
    '2019-06-09T12:00:00Z',
    '2019-06-10T12:00:00Z'
  ];

  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % timelineDates.length);
    }, 3000); // Change every 3 seconds

    return () => clearInterval(interval);
  }, [isPlaying, timelineDates.length]);

  const timestamp = timelineDates[currentIndex];
  const label = new Date(timestamp).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
  const speedLabel = isPlaying ? 'Playing' : 'Paused';

  return {
    timestamp,
    label,
    speedLabel,
    currentIndex,
    setCurrentIndex,
    isPlaying,
    setIsPlaying
  };
};