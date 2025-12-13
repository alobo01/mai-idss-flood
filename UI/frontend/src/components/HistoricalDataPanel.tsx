import React, { useMemo, useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  CalendarClock,
  History,
  Settings,
  Eye,
  EyeOff,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { useBackendData } from '@/hooks/useBackendData';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
  Area,
  ComposedChart,
  Bar
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || '/api';

interface ChartDataPoint {
  date: string;
  dateObj: Date;
  actual: number | null;
  predicted_1d: number | null;
  predicted_1d_lower: number | null;
  predicted_1d_upper: number | null;
  predicted_2d: number | null;
  predicted_2d_lower: number | null;
  predicted_2d_upper: number | null;
  predicted_3d: number | null;
  predicted_3d_lower: number | null;
  predicted_3d_upper: number | null;
  flood_prob_1d: number | null;
  flood_prob_2d: number | null;
  flood_prob_3d: number | null;
  aboveThreshold: boolean;
}

export const HistoricalDataPanel: React.FC = () => {
  const { rawData, history, loading, error } = useBackendData();
  const [yearFilter, setYearFilter] = useState<string>('all');
  const [monthFilter, setMonthFilter] = useState<string>('all');
  const [selectedPredictions, setSelectedPredictions] = useState<Set<number>>(new Set([1, 2, 3]));
  const [showConfidenceIntervals, setShowConfidenceIntervals] = useState<boolean>(true);
  const [threshold, setThreshold] = useState<number>(0.3);
  const [showThreshold, setShowThreshold] = useState<boolean>(true);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const [scriptAvailable, setScriptAvailable] = useState<boolean | null>(null);

  const years = useMemo(() => {
    const ys = new Set<string>();
    rawData.forEach(r => ys.add(new Date(r.date).getFullYear().toString()));
    return Array.from(ys).sort();
  }, [rawData]);

  const months = ['01','02','03','04','05','06','07','08','09','10','11','12'];

  const chartData = useMemo(() => {
    const dataMap = new Map<string, ChartDataPoint>();

    // Add raw data
    rawData.forEach(row => {
      const dateStr = row.date;
      const dateObj = new Date(dateStr);
      const y = dateObj.getFullYear().toString();
      const m = (dateObj.getMonth() + 1).toString().padStart(2, '0');

      if ((yearFilter === 'all' || y === yearFilter) &&
          (monthFilter === 'all' || m === monthFilter)) {
        dataMap.set(dateStr, {
          date: dateStr,
          dateObj,
          actual: row.target_level_max,
          predicted_1d: null,
          predicted_1d_lower: null,
          predicted_1d_upper: null,
          predicted_2d: null,
          predicted_2d_lower: null,
          predicted_2d_upper: null,
          predicted_3d: null,
          predicted_3d_lower: null,
          predicted_3d_upper: null,
          flood_prob_1d: null,
          flood_prob_2d: null,
          flood_prob_3d: null,
          aboveThreshold: false
        });
      }
    });

    // Add prediction data
    history.forEach(pred => {
      const dateStr = pred.date;
      const existing = dataMap.get(dateStr);

      if (existing) {
        const leadKey = `predicted_${pred.days_ahead}d` as keyof ChartDataPoint;
        const lowerKey = `predicted_${pred.days_ahead}d_lower` as keyof ChartDataPoint;
        const upperKey = `predicted_${pred.days_ahead}d_upper` as keyof ChartDataPoint;
        const probKey = `flood_prob_${pred.days_ahead}d` as keyof ChartDataPoint;

        (existing as any)[leadKey] = pred.predicted_level;
        (existing as any)[lowerKey] = pred.lower_bound_80 ?? null;
        (existing as any)[upperKey] = pred.upper_bound_80 ?? null;
        (existing as any)[probKey] = pred.flood_probability ? pred.flood_probability * 100 : null;
        existing.aboveThreshold = existing.aboveThreshold || ((pred.flood_probability || 0) >= threshold);
      }
    });

    return Array.from(dataMap.values()).sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime());
  }, [rawData, history, yearFilter, monthFilter, threshold]);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const r = await fetch(`${API_URL}/scripts/predict-all/available`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = await r.json();
        if (!cancelled) setScriptAvailable(Boolean(j.available));
      } catch (e: any) {
        if (!cancelled) setScriptAvailable(false);
      }
    };
    check();
    return () => { cancelled = true; };
  }, []);

  const togglePrediction = (days: number) => {
    const newSet = new Set(selectedPredictions);
    if (newSet.has(days)) {
      newSet.delete(days);
    } else {
      newSet.add(days);
    }
    setSelectedPredictions(newSet);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-semibold">{`Date: ${new Date(label).toLocaleDateString()}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value != null ? `${entry.value.toFixed(2)} ft` : 'N/A'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const ProbabilityTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-semibold">{`Date: ${new Date(label).toLocaleDateString()}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value != null ? `${entry.value.toFixed(1)}%` : 'N/A'}
            </p>
          ))}
        </div>
      );
    }
    return null;
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
            {/* Controls */}
            <div className="flex flex-wrap items-center gap-4 text-sm">
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
            </div>

            {/* Chart Controls */}
            <div className="border-t pt-4">
              <div className="flex items-center gap-2 mb-3">
                <Settings className="h-4 w-4" />
                <span className="font-medium text-sm">Chart Settings</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                {/* Prediction Selection */}
                <div className="space-y-2">
                  <label className="text-slate-700 font-medium">Show Predictions</label>
                  <div className="space-y-1">
                    {[1, 2, 3].map(days => (
                      <label key={days} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedPredictions.has(days)}
                          onChange={() => togglePrediction(days)}
                          className="rounded"
                        />
                        <span className="flex items-center gap-1">
                          {days} day{days > 1 ? 's' : ''} ahead
                          <div className={`w-3 h-3 rounded`} style={{
                            backgroundColor: days === 1 ? '#3b82f6' : days === 2 ? '#10b981' : '#f59e0b'
                          }}></div>
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Confidence Intervals */}
                <div className="space-y-2">
                  <label className="text-slate-700 font-medium">Confidence Intervals</label>
                  <Button
                    variant={showConfidenceIntervals ? "default" : "outline"}
                    size="sm"
                    onClick={() => setShowConfidenceIntervals(!showConfidenceIntervals)}
                    className="flex items-center gap-2"
                  >
                    {showConfidenceIntervals ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    {showConfidenceIntervals ? 'Visible' : 'Hidden'}
                  </Button>
                </div>

                {/* Threshold */}
                <div className="space-y-2">
                  <label className="text-slate-700 font-medium">Flood Threshold</label>
                  <div className="space-y-1">
                    <input
                      type="range"
                      min="0.1"
                      max="0.9"
                      step="0.1"
                      value={threshold}
                      onChange={e => setThreshold(parseFloat(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-slate-600">
                      <span>10%</span>
                      <span className="font-medium">{(threshold * 100).toFixed(0)}%</span>
                      <span>90%</span>
                    </div>
                  </div>
                </div>

                {/* Show Threshold */}
                <div className="space-y-2">
                  <label className="text-slate-700 font-medium">Threshold Alert</label>
                  <Button
                    variant={showThreshold ? "default" : "outline"}
                    size="sm"
                    onClick={() => setShowThreshold(!showThreshold)}
                    className="flex items-center gap-2"
                  >
                    <AlertTriangle className="h-4 w-4" />
                    {showThreshold ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
              </div>
            </div>

            {/* Predict Button -> show external CLI script availability */}
            <div className="flex justify-end pt-2 border-t">
              <div className="flex items-center gap-4">
                <div className="text-sm text-slate-700">Historical backfill:</div>
                {scriptAvailable === null && <div className="text-sm text-slate-500">Checking…</div>}
                {scriptAvailable === false && (
                  <div className="text-sm text-red-600 flex items-center gap-2"> <AlertTriangle className="h-4 w-4" /> Not available</div>
                )}
                {scriptAvailable === true && (
                  <div className="text-sm text-green-600 flex items-center gap-2">Available (run via <code>scripts/predict_all.py</code>)</div>
                )}
              </div>
              {actionStatus && <span className="text-xs text-slate-600 ml-4">{actionStatus}</span>}
            </div>

            {/* Line Chart */}
            <div className="border rounded-lg p-4 bg-white">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-4 w-4" />
                <span className="font-medium">Water Level Predictions</span>
                <Badge variant="secondary">{chartData.length} points</Badge>
              </div>

              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    stroke="#666"
                  />
                  <YAxis
                    label={{ value: 'Water Level (ft)', angle: -90, position: 'insideLeft' }}
                    stroke="#666"
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />

                  {/* Actual values */}
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#1f2937"
                    strokeWidth={2}
                    dot={false}
                    name="Actual"
                  />

                  {/* Predictions with confidence intervals */}
                  {selectedPredictions.has(1) && (
                    <>
                      {showConfidenceIntervals && (
                        <Area
                          type="monotone"
                          dataKey="predicted_1d_upper"
                          stackId="1"
                          stroke="#3b82f6"
                          fill="#3b82f6"
                          fillOpacity={0.1}
                          strokeOpacity={0}
                          name="1d Upper CI"
                        />
                      )}
                      <Line
                        type="monotone"
                        dataKey="predicted_1d"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                        name="1 Day Ahead"
                      />
                      {showConfidenceIntervals && (
                        <Area
                          type="monotone"
                          dataKey="predicted_1d_lower"
                          stackId="1"
                          stroke="#3b82f6"
                          fill="#3b82f6"
                          fillOpacity={0.1}
                          strokeOpacity={0}
                          name="1d Lower CI"
                        />
                      )}
                    </>
                  )}

                  {selectedPredictions.has(2) && (
                    <>
                      {showConfidenceIntervals && (
                        <Area
                          type="monotone"
                          dataKey="predicted_2d_upper"
                          stackId="2"
                          stroke="#10b981"
                          fill="#10b981"
                          fillOpacity={0.1}
                          strokeOpacity={0}
                          name="2d Upper CI"
                        />
                      )}
                      <Line
                        type="monotone"
                        dataKey="predicted_2d"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={false}
                        name="2 Days Ahead"
                      />
                      {showConfidenceIntervals && (
                        <Area
                          type="monotone"
                          dataKey="predicted_2d_lower"
                          stackId="2"
                          stroke="#10b981"
                          fill="#10b981"
                          fillOpacity={0.1}
                          strokeOpacity={0}
                          name="2d Lower CI"
                        />
                      )}
                    </>
                  )}

                  {selectedPredictions.has(3) && (
                    <>
                      {showConfidenceIntervals && (
                        <Area
                          type="monotone"
                          dataKey="predicted_3d_upper"
                          stackId="3"
                          stroke="#f59e0b"
                          fill="#f59e0b"
                          fillOpacity={0.1}
                          strokeOpacity={0}
                          name="3d Upper CI"
                        />
                      )}
                      <Line
                        type="monotone"
                        dataKey="predicted_3d"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        dot={false}
                        name="3 Days Ahead"
                      />
                      {showConfidenceIntervals && (
                        <Area
                          type="monotone"
                          dataKey="predicted_3d_lower"
                          stackId="3"
                          stroke="#f59e0b"
                          fill="#f59e0b"
                          fillOpacity={0.1}
                          strokeOpacity={0}
                          name="3d Lower CI"
                        />
                      )}
                    </>
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Probability Chart */}
            <div className="border rounded-lg p-4 bg-white">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-medium">Flood Probability (%)</span>
                {showThreshold && (
                  <Badge variant={threshold > 0.5 ? "destructive" : "secondary"}>
                    Threshold: {(threshold * 100).toFixed(0)}%
                  </Badge>
                )}
              </div>

              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    stroke="#666"
                  />
                  <YAxis
                    label={{ value: 'Flood Probability (%)', angle: -90, position: 'insideLeft' }}
                    domain={[0, 100]}
                    stroke="#666"
                  />
                  <Tooltip content={<ProbabilityTooltip />} />
                  <Legend />

                  {/* Threshold line */}
                  {showThreshold && (
                    <Line
                      type="monotone"
                      dataKey={() => threshold * 100}
                      stroke="#ef4444"
                      strokeDasharray="5 5"
                      dot={false}
                      name={`Threshold (${(threshold * 100).toFixed(0)}%)`}
                    />
                  )}

                  {/* Probability lines */}
                  {selectedPredictions.has(1) && (
                    <Line
                      type="monotone"
                      dataKey="flood_prob_1d"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                      name="1 Day Prob"
                    />
                  )}

                  {selectedPredictions.has(2) && (
                    <Line
                      type="monotone"
                      dataKey="flood_prob_2d"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                      name="2 Days Prob"
                    />
                  )}

                  {selectedPredictions.has(3) && (
                    <Line
                      type="monotone"
                      dataKey="flood_prob_3d"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      dot={false}
                      name="3 Days Prob"
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Threshold Alert Periods */}
            {showThreshold && (
              <div className="border rounded-lg p-4 bg-white">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="font-medium">High Flood Risk Periods</span>
                  <Badge variant="destructive">
                    &gt;{(threshold * 100).toFixed(0)}%
                  </Badge>
                </div>

                <div className="space-y-2 text-sm">
                  {chartData.filter(d => d.aboveThreshold).length === 0 ? (
                    <p className="text-slate-500">No periods above threshold detected</p>
                  ) : (
                    chartData
                      .filter(d => d.aboveThreshold)
                      .map((d, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-red-50 rounded">
                          <span className="font-medium">{d.dateObj.toLocaleDateString()}</span>
                          <div className="flex gap-4">
                            {d.flood_prob_1d !== null && (
                              <span className="text-blue-600">1d: {d.flood_prob_1d.toFixed(1)}%</span>
                            )}
                            {d.flood_prob_2d !== null && (
                              <span className="text-green-600">2d: {d.flood_prob_2d.toFixed(1)}%</span>
                            )}
                            {d.flood_prob_3d !== null && (
                              <span className="text-amber-600">3d: {d.flood_prob_3d.toFixed(1)}%</span>
                            )}
                          </div>
                        </div>
                      ))
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};
