import { useEffect, useMemo, useState } from 'react';
import { BackendPredictResponse, RawDataRow, PredictionHistoryItem } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export function useBackendData() {
  const [predictions, setPredictions] = useState<BackendPredictResponse | null>(null);
  const [rawData, setRawData] = useState<RawDataRow[]>([]);
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      setLoading(true);
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
          setRawData(rawJson.rows || []);
          setHistory(histJson.rows || []);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e.message || 'Request failed');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchData();
    return () => {
      cancelled = true;
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
