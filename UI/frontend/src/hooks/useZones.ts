import { useEffect, useState } from 'react';
import { GaugePoint, ZoneRow, GeoFeatureCollection } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export function useZones() {
  const [zones, setZones] = useState<ZoneRow[]>([]);
  const [zonesGeo, setZonesGeo] = useState<GeoFeatureCollection | null>(null);
  const [gauges, setGauges] = useState<GaugePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
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
        if (!cancelled) {
          setZones(zJson.rows || []);
          setGauges(gJson.rows || []);
          setZonesGeo(zgJson || null);
        }
      } catch (e: any) {
        if (!cancelled) setError(e.message || 'Failed to load zones');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  return { zones, zonesGeo, gauges, loading, error };
}
