import { useEffect, useMemo, useState } from 'react';
import { BackendPredictResponse, RawDataRow, PredictionHistoryItem } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || '/api';

function extractRows<T>(json: any): T[] {
  const rows = json?.data?.rows ?? json?.rows ?? [];
  return Array.isArray(rows) ? (rows as T[]) : [];
}

function normalizePredictionHistory(rows: any[]): PredictionHistoryItem[] {
  return rows
    .map((r: any) => ({
      date: r?.forecast_date ?? r?.date ?? '',
      predicted_level: r?.predicted_level ?? null,
      lower_bound_80: r?.lower_bound_80 ?? null,
      upper_bound_80: r?.upper_bound_80 ?? null,
      flood_probability: r?.flood_probability ?? null,
      days_ahead: r?.lead_time_days ?? r?.days_ahead ?? 0,
      created_at: r?.created_at ?? '',
    }))
    .filter((r) => Boolean(r.date) && typeof r.days_ahead === 'number' && r.days_ahead > 0);
}

export function useBackendData() {
  const [predictions, setPredictions] = useState<BackendPredictResponse | null>(null);
  const [rawData, setRawData] = useState<RawDataRow[]>([]);
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let intervalId: number | undefined;
    let isFirstLoad = true;

    async function fetchData() {
      // Only show loading on first load, not on periodic updates
      if (isFirstLoad) {
        setLoading(true);
      }
      setError(null);
      try {
        const [predRes, rawRes, histRes] = await Promise.all([
          fetch(`${API_URL}/predict`),
          fetch(`${API_URL}/raw-data`),
          fetch(`${API_URL}/prediction-history?limit=120`),
        ]);

        if (!predRes.ok) throw new Error(`Prediction fetch failed (${predRes.status})`);
        if (!rawRes.ok) throw new Error(`Raw data fetch failed (${rawRes.status})`);
        if (!histRes.ok) throw new Error(`History fetch failed (${histRes.status})`);

        const predJson: BackendPredictResponse = await predRes.json();
        const rawJson = await rawRes.json();
        const histJson = await histRes.json();

        if (!cancelled) {
          setPredictions(predJson);
          setRawData(extractRows<RawDataRow>(rawJson));
          setHistory(normalizePredictionHistory(extractRows<any>(histJson)));
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e.message || 'Request failed');
        }
      } finally {
        if (!cancelled && isFirstLoad) {
          setLoading(false);
          isFirstLoad = false;
        }
      }
    }

    // Initial fetch
    fetchData();

    // Poll every 10 seconds
    intervalId = window.setInterval(() => {
      fetchData();
    }, 10000);

    return () => {
      cancelled = true;
      if (intervalId !== undefined) window.clearInterval(intervalId);
    };
  }, []);

  const latestObservation = useMemo(() => {
    if (!rawData.length) return null;
    return rawData[rawData.length - 1];
  }, [rawData]);

  return {
    predictions,
    rawData,
    history,
    latestObservation,
    loading,
    error,
  };
}
