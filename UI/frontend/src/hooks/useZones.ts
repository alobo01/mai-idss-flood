import { useEffect, useState } from 'react';
import { GaugePoint, ZoneRow, GeoFeatureCollection } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export function useZones() {
  const [zones, setZones] = useState<ZoneRow[]>([]);
  const [zonesGeo, setZonesGeo] = useState<GeoFeatureCollection | null>(null);
  const [gauges, setGauges] = useState<GaugePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [zRes, gRes, zgRes] = await Promise.all([
        fetch(`${API_URL}/zones`),
        fetch(`${API_URL}/gauges`),
        fetch(`${API_URL}/zones-geo`),
      ]);
      if (!zRes.ok) throw new Error(`Zones fetch failed (${zRes.status})`);
      if (!gRes.ok) throw new Error(`Gauges fetch failed (${gRes.status})`);
      if (!zgRes.ok) throw new Error(`Zone geo fetch failed (${zgRes.status})`);
      const zJson = await zRes.json();
      const gJson = await gRes.json();
      const zgJson = await zgRes.json();
      setZones(zJson.rows || []);
      setGauges(gJson.rows || []);
      setZonesGeo(zgJson || null);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load zones');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial load
    fetchData();

    // Set up interval for every 10 seconds (10000ms)
    const interval = setInterval(() => {
      fetchData();
    }, 10000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  return { zones, zonesGeo, gauges, loading, error };
}
