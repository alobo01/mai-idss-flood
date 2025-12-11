import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { AlertTriangle, Clock, Activity, Droplets, TrendingUp, ShieldHalf, Waves } from 'lucide-react';
import { useBackendData } from '@/hooks/useBackendData';
import { BackendPrediction, PredictionHistoryItem } from '@/types';

function formatFt(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return '—';
  return `${value.toFixed(2)} ft`;
}

const Sparkline: React.FC<{ series: number[]; predictions?: number[]; upper?: number[]; lower?: number[] }> = ({ series, predictions = [], upper = [], lower = [] }) => {
  const width = 900;
  const height = 180;
  const margin = 12;
  const all = [...series, ...predictions, ...upper, ...lower].filter((v) => typeof v === 'number');
  if (!all.length) return null;
  const min = Math.min(...all);
  const max = Math.max(...all);
  const range = max - min || 1;
  const toPoint = (v: number, idx: number, total: number) => {
    const x = margin + (idx / Math.max(total - 1, 1)) * (width - margin * 2);
    const y = height - margin - ((v - min) / range) * (height - margin * 2);
    return `${x},${y}`;
  };
  const obsPts = series.map((v, i) => toPoint(v, i, series.length + predictions.length));
  const predPts = predictions.map((v, i) => toPoint(v, series.length - 1 + i + 1, series.length + predictions.length));
  const upperPoly = upper.map((v, i) => toPoint(v, series.length - 1 + i + 1, series.length + predictions.length));
  const lowerPoly = lower.map((v, i) => toPoint(v, series.length - 1 + i + 1, series.length + predictions.length)).reverse();
  const lastObservedPt = series.length ? toPoint(series[series.length - 1], series.length - 1, series.length + predictions.length) : null;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full rounded-lg border border-slate-200 bg-gradient-to-b from-slate-50 to-white shadow-inner">
      {upperPoly.length === lowerPoly.length && upperPoly.length > 0 && (
        <polygon
          points={[...upperPoly, ...lowerPoly].join(' ')}
          fill="#0ea5e92b"
          stroke="#0ea5e9"
          strokeWidth="1"
          strokeOpacity="0.4"
        />
      )}
      <polyline fill="none" stroke="#0f172a" strokeWidth="2.5" strokeLinecap="round" points={obsPts.join(' ')} />
      {predPts.length > 0 && (
        <>
          {lastObservedPt && (
            <polyline
              fill="none"
              stroke="#0891b2"
              strokeWidth="2.5"
              strokeDasharray="6 6"
              points={[lastObservedPt, predPts[0]].join(' ')}
            />
          )}
          <polyline fill="none" stroke="#0891b2" strokeWidth="2.5" strokeDasharray="6 6" points={predPts.join(' ')} />
        </>
      )}
      <line x1={margin} x2={width - margin} y1={height - margin} y2={height - margin} stroke="#e2e8f0" strokeWidth="1" />
    </svg>
  );
};

export function StLouisFloodPanel() {
  const { predictions, rawData, latestObservation, history, loading, error } = useBackendData();
  const forecastCards = predictions?.predictions || [];

  const historySeries = useMemo(() => rawData.map(r => r.target_level_max), [rawData]);
  const predictedSeries = useMemo(() => forecastCards.map(p => p.forecast?.median ?? NaN).filter(n => !Number.isNaN(n)), [forecastCards]);
  const predictedUpper = useMemo(() => forecastCards.map(p => p.prediction_interval_80pct?.upper ?? NaN).filter(n => !Number.isNaN(n)), [forecastCards]);
  const predictedLower = useMemo(() => forecastCards.map(p => p.prediction_interval_80pct?.lower ?? NaN).filter(n => !Number.isNaN(n)), [forecastCards]);

  const levelTrend = useMemo(() => {
    if (rawData.length < 2) return null;
    const last = rawData[rawData.length - 1].target_level_max;
    const prev = rawData[rawData.length - 2].target_level_max;
    return last - prev;
  }, [rawData]);

  const bottomTable = useMemo(() => {
    const recent = rawData.slice(-10);
    const predictedRows = forecastCards.map(p => ({
      date: p.forecast_date,
      target_level_max: p.forecast?.median ?? null,
      hermann_level: null,
      grafton_level: null,
      daily_precip: null,
      isForecast: true,
      lead: p.lead_time_days,
      pi: p.prediction_interval_80pct,
      prob: p.flood_risk?.probability,
    }));
    return [...recent.map(r => ({ ...r, isForecast: false } as any)), ...predictedRows];
  }, [rawData, forecastCards]);

  const historyRows = useMemo(() => history.slice(0, 30), [history]);

  return (
    <Card className="border border-gray-200 shadow-lg bg-white">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            St. Louis River Dashboard
          </CardTitle>
          <p className="text-sm text-gray-600">
            Live gauges + 1–3 day forecasts with uncertainty
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <Badge variant="secondary" className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            Backend
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {predictions?.timestamp ? new Date(predictions.timestamp).toLocaleString() : '—'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {loading && <div className="text-sm text-gray-500">Loading real data…</div>}
        {error && <div className="text-sm text-red-600">Error: {error}</div>}

        {!loading && !error && (
          <>
            {/* Snapshot */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="p-4 border border-gray-200/80 shadow-sm bg-white/90">
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Latest level</div>
                <div className="text-3xl font-semibold text-gray-900">{formatFt(latestObservation?.target_level_max)}</div>
                <div className="text-xs text-gray-500">St. Louis · {latestObservation?.date ? new Date(latestObservation.date).toLocaleDateString() : '—'}</div>
              </Card>
              <Card className="p-4 border border-gray-200/80 shadow-sm bg-white/90">
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Day-over-day</div>
                <div className="text-3xl font-semibold text-amber-700 flex items-center gap-1">
                  <TrendingUp className="h-4 w-4" />
                  {levelTrend !== null ? `${levelTrend >= 0 ? '+' : ''}${levelTrend?.toFixed(2)} ft` : '—'}
                </div>
                <div className="text-xs text-gray-500">Positive = rising</div>
              </Card>
              <Card className="p-4 border border-gray-200/80 shadow-sm bg-white/90">
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Hermann gauge</div>
                <div className="text-3xl font-semibold text-gray-900">{formatFt(latestObservation?.hermann_level)}</div>
                <div className="text-xs text-gray-500">Upstream signal</div>
              </Card>
              <Card className="p-4 border border-gray-200/80 shadow-sm bg-white/90">
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">24h precip</div>
                <div className="text-3xl font-semibold text-sky-700 flex items-center gap-1">
                  <Droplets className="h-4 w-4" />
                  {latestObservation?.daily_precip !== undefined ? `${latestObservation.daily_precip.toFixed(2)} mm` : '—'}
                </div>
                <div className="text-xs text-gray-500">Local loading</div>
              </Card>
            </div>

            {/* History + forecasts chart */}
            {historySeries.length > 0 && (
              <Card className="p-4 border border-gray-200/80 bg-white/90 shadow-sm">
                <div className="flex items-center justify-between text-sm text-gray-700 mb-3">
                  <span className="font-semibold">30-day history + forecast cone</span>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-slate-800 rounded" /> Observed</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-sky-600 rounded border border-sky-600 border-dashed" /> Forecast</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-2 bg-sky-200/80 rounded-sm" /> 80% PI</span>
                  </div>
                </div>
                <Sparkline series={historySeries} predictions={predictedSeries} upper={predictedUpper} lower={predictedLower} />
              </Card>
            )}

            {/* Forecast cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {forecastCards.map((p: BackendPrediction) => (
                <Card key={p.lead_time_days} className="p-4 border border-gray-200/80 bg-gradient-to-br from-white to-sky-50 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-semibold text-gray-800">{p.lead_time_days}-day forecast</div>
                    <Badge variant="outline">{new Date(p.forecast_date).toLocaleDateString()}</Badge>
                  </div>
                  {p.error ? (
                    <div className="text-sm text-red-600">{p.error}</div>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-3xl font-semibold text-gray-900">{formatFt(p.forecast?.median)}</div>
                      <div className="flex items-center text-xs text-gray-600 gap-2">
                        <span className="font-semibold text-gray-800">PI80</span>
                        <span>{p.prediction_interval_80pct ? `${p.prediction_interval_80pct.lower.toFixed(2)} – ${p.prediction_interval_80pct.upper.toFixed(2)} ft` : '—'}</span>
                        <span className="text-gray-400">({p.prediction_interval_80pct?.width?.toFixed(2)} ft)</span>
                      </div>
                      <div className="text-xs text-gray-600">
                        Flood probability: {p.flood_risk?.probability != null ? `${(p.flood_risk.probability * 100).toFixed(1)}%` : '—'} {p.flood_risk?.risk_indicator}
                      </div>
                    </div>
                  )}
                </Card>
              ))}
            </div>

            {/* Observations + tail */}
            <div className="border-2 border-border rounded-lg overflow-hidden bg-card shadow-md">
              <div className="card-header-emergency">
                <div className="flex items-center gap-3">
                  <Waves className="h-5 w-5 text-foreground" aria-hidden="true" />
                  <span className="text-lg font-bold text-foreground">Recent observations & forecast tail</span>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full table-emergency">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">St. Louis</th>
                      <th scope="col">Hermann</th>
                      <th scope="col">Grafton</th>
                      <th scope="col">Precip</th>
                      <th scope="col">PI80</th>
                      <th scope="col">Flood prob</th>
                      <th scope="col">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bottomTable.map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-muted/50">
                        <td>{new Date(row.date).toLocaleDateString()}</td>
                        <td>{row.target_level_max != null ? `${row.target_level_max.toFixed(2)} ft` : '—'}</td>
                        <td>{row.hermann_level != null ? `${row.hermann_level.toFixed(2)} ft` : '—'}</td>
                        <td>{row.grafton_level != null ? `${row.grafton_level.toFixed(2)} ft` : '—'}</td>
                        <td>{row.daily_precip != null ? `${row.daily_precip.toFixed(2)} mm` : '—'}</td>
                        <td>{row.pi ? `${row.pi.lower.toFixed(2)}–${row.pi.upper.toFixed(2)}` : '—'}</td>
                        <td>{row.prob != null ? `${(row.prob * 100).toFixed(1)}%` : '—'}</td>
                        <td>
                          {row.isForecast ? (
                            <Badge variant="outline" className="button-emergency status-indicator">Forecast +{row.lead}d</Badge>
                          ) : (
                            <Badge variant="secondary" className="button-emergency status-indicator">Observed</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Stored prediction history */}
            {historyRows.length > 0 && (
              <div className="border-2 border-border rounded-lg overflow-hidden bg-card shadow-md">
                <div className="card-header-emergency">
                  <div className="flex items-center gap-3">
                    <ShieldHalf className="h-5 w-5 text-foreground" aria-hidden="true" />
                    <span className="text-lg font-bold text-foreground">Stored predictions (last {historyRows.length})</span>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full table-emergency">
                    <thead>
                      <tr>
                        <th scope="col">Forecast Date</th>
                        <th scope="col">Lead</th>
                        <th scope="col">Predicted</th>
                        <th scope="col">Flood prob</th>
                        <th scope="col">Stored at</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historyRows.map((row: PredictionHistoryItem, idx) => (
                        <tr key={idx} className="hover:bg-muted/50">
                          <td>{new Date(row.date).toLocaleDateString()}</td>
                          <td>+{row.days_ahead}d</td>
                          <td>{row.predicted_level != null ? `${row.predicted_level.toFixed(2)} ft` : '—'}</td>
                          <td>{row.flood_probability != null ? `${(row.flood_probability * 100).toFixed(1)}%` : '—'}</td>
                          <td className="text-sm text-muted-foreground">{new Date(row.created_at).toLocaleString()}</td>
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
}
