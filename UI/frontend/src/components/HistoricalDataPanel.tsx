import React, { useMemo, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CalendarClock, History, Send } from 'lucide-react';
import { useBackendData } from '@/hooks/useBackendData';
import { Button } from '@/components/ui/button';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export const HistoricalDataPanel: React.FC = () => {
  const { rawData, history, loading, error } = useBackendData();
  const [yearFilter, setYearFilter] = useState<string>('all');
  const [monthFilter, setMonthFilter] = useState<string>('all');
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const years = useMemo(() => {
    const ys = new Set<string>();
    rawData.forEach(r => ys.add(new Date(r.date).getFullYear().toString()));
    return Array.from(ys).sort();
  }, [rawData]);

  const months = ['01','02','03','04','05','06','07','08','09','10','11','12'];

  const filtered = useMemo(() => {
    return rawData.filter(r => {
      const d = new Date(r.date);
      const y = d.getFullYear().toString();
      const m = (d.getMonth() + 1).toString().padStart(2, '0');
      return (yearFilter === 'all' || y === yearFilter) &&
             (monthFilter === 'all' || m === monthFilter);
    });
  }, [rawData, yearFilter, monthFilter]);

  const handlePredictAll = async () => {
    setActionStatus('Sending request…');
    try {
      const res = await fetch(`${API_URL}/predict-all`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setActionStatus(json.message || 'Request sent');
    } catch (e: any) {
      setActionStatus(`Failed: ${e.message}`);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="h-5 w-5" />
          Historical Data Explorer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && <div className="text-sm text-slate-500">Loading…</div>}
        {error && <div className="text-sm text-red-600">Error: {error}</div>}

        {!loading && !error && (
          <>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <div className="flex items-center gap-2">
                <CalendarClock className="h-4 w-4 text-slate-600" />
                <label className="text-slate-700">Year</label>
                <select value={yearFilter} onChange={e => setYearFilter(e.target.value)} className="border rounded px-2 py-1 text-sm">
                  <option value="all">All</option>
                  {years.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-slate-700">Month</label>
                <select value={monthFilter} onChange={e => setMonthFilter(e.target.value)} className="border rounded px-2 py-1 text-sm">
                  <option value="all">All</option>
                  {months.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Button variant="default" size="sm" onClick={handlePredictAll} className="flex items-center gap-1">
                  <Send className="h-4 w-4" />
                  Predict for all previous data
                </Button>
                {actionStatus && <span className="text-xs text-slate-600">{actionStatus}</span>}
              </div>
            </div>

            <div className="border rounded-md overflow-hidden bg-white/70">
              <div className="px-4 py-2 bg-slate-900 text-white text-sm font-semibold flex items-center gap-2">
                <CalendarClock className="h-4 w-4" />
                {filtered.length} records
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      <th className="px-3 py-2 text-left">Date</th>
                      <th className="px-3 py-2 text-left">St. Louis</th>
                      <th className="px-3 py-2 text-left">Hermann</th>
                      <th className="px-3 py-2 text-left">Grafton</th>
                      <th className="px-3 py-2 text-left">Precip</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((row, idx) => (
                      <tr key={idx} className="border-t border-slate-200">
                        <td className="px-3 py-2">{new Date(row.date).toLocaleDateString()}</td>
                        <td className="px-3 py-2">{row.target_level_max.toFixed(2)} ft</td>
                        <td className="px-3 py-2">{row.hermann_level.toFixed(2)} ft</td>
                        <td className="px-3 py-2">{row.grafton_level.toFixed(2)} ft</td>
                        <td className="px-3 py-2">{row.daily_precip.toFixed(2)} mm</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {history.length > 0 && (
              <div className="border rounded-md overflow-hidden bg-white/70">
                <div className="px-4 py-2 bg-slate-900 text-white text-sm font-semibold flex items-center gap-2">
                  <Badge variant="secondary">Stored predictions</Badge>
                  {history.length}
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-slate-100 text-slate-700">
                      <tr>
                        <th className="px-3 py-2 text-left">Forecast Date</th>
                        <th className="px-3 py-2 text-left">Lead</th>
                        <th className="px-3 py-2 text-left">Predicted</th>
                        <th className="px-3 py-2 text-left">Flood prob</th>
                        <th className="px-3 py-2 text-left">Stored at</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((row, idx) => (
                        <tr key={idx} className="border-t border-slate-200">
                          <td className="px-3 py-2">{new Date(row.date).toLocaleDateString()}</td>
                          <td className="px-3 py-2">+{row.days_ahead}d</td>
                          <td className="px-3 py-2">{row.predicted_level != null ? `${row.predicted_level.toFixed(2)} ft` : '—'}</td>
                          <td className="px-3 py-2">{row.flood_probability != null ? `${(row.flood_probability * 100).toFixed(1)}%` : '—'}</td>
                          <td className="px-3 py-2 text-xs text-slate-500">{new Date(row.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};
