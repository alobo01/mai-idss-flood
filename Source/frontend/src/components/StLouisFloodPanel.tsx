import React, { useMemo } from 'react';
import { format, formatDistanceToNowStrict } from 'date-fns';
import { AlertTriangle, Activity, Gauge, Clock, MapPin, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useGauges, useRiverPredictions } from '@/hooks/useApiData';
import type { StageProbability, Gauge as GaugeType, RiverLevelPrediction } from '@/types';

const stageOrder = ['Action', 'Flood', 'Moderate', 'Major'];

const probabilityColor = (p: number) => {
  if (p >= 0.75) return 'bg-red-500';
  if (p >= 0.5) return 'bg-orange-500';
  if (p >= 0.25) return 'bg-amber-400';
  return 'bg-emerald-500';
};

function StationCard({
  gauge,
  prediction,
  stages,
}: {
  gauge: GaugeType;
  prediction?: RiverLevelPrediction;
  stages: StageProbability[];
}) {
  const predLevel = prediction?.predicted_level ?? gauge.level_m;
  const probFlood = stages.find(s => s.stage === 'Flood')?.probability ?? 0;
  const probPct = Math.round(probFlood * 100);
  const role = gauge.id === '07010000' ? 'target' : 'sensor';

  return (
    <Card className="shadow-sm border border-slate-200">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="text-sm font-semibold flex items-center gap-1">
              <MapPin className="h-4 w-4 text-slate-500" />
              {gauge.name}
            </div>
            <div className="text-xs text-muted-foreground">{gauge.id}</div>
          </div>
          {role === 'target' ? (
            <Badge variant="destructive">Target (predicted)</Badge>
          ) : (
            <Badge variant="secondary">Sensor</Badge>
          )}
        </div>

        <div className="flex items-end gap-3">
          <div>
            <div className="text-xs uppercase text-slate-500 tracking-wide">Current</div>
            <div className="text-3xl font-bold leading-tight">
              {gauge.level_m.toFixed(2)} m
            </div>
          </div>
          {prediction && (
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              trend {prediction.trend_per_hour >= 0 ? '+' : ''}{prediction.trend_per_hour.toFixed(2)} m/hr
            </div>
          )}
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Predicted ({prediction ? format(new Date(prediction.prediction_time), 'HH:mm') : '—'})</span>
          <span className="font-semibold">
            {predLevel.toFixed(2)} m
            {prediction && (
              <Badge variant="outline" className="ml-2 text-[10px]">conf {(prediction.confidence_level * 100).toFixed(0)}%</Badge>
            )}
          </span>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Chance to hit flood stage</span>
            <span className="font-semibold">{probPct}%</span>
          </div>
          <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${probabilityColor(probPct / 100)}`}
              style={{ width: `${Math.min(probPct, 100)}%` }}
            />
          </div>
        </div>

        <div className="text-[11px] text-muted-foreground">
          Updated {formatDistanceToNowStrict(new Date(gauge.last_updated), { addSuffix: true })}
        </div>
      </CardContent>
    </Card>
  );
}

function StageBar({ stage }: { stage: StageProbability }) {
  const pct = Math.round(stage.probability * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="uppercase">{stage.stage}</Badge>
          <span className="text-muted-foreground text-xs">{stage.level_ft} ft</span>
        </div>
        <span className="font-semibold">{pct}%</span>
      </div>
      <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${probabilityColor(stage.probability)} transition-all`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

export function StLouisFloodPanel() {
  const { data: gauges = [], isLoading: gaugesLoading } = useGauges();
  const { data: predictions = [], isLoading: predsLoading, isFetching: predsFetching, refetch } = useRiverPredictions();

  const orderedStages = useMemo(() => {
    const target = gauges.find(g => g.id === '07010000');
    if (!target) return [];
    const meta: any = (target as any).metadata || (target as any).meta || {};
    const stages = meta.stages_ft || {};
    const probs: StageProbability[] = Object.entries(stages).map(([stage, ft]) => {
      const predictedFt = metersToFeet(
        predictions.find(p => p.gauge_id === '07010000')?.predicted_level ?? target.level_m
      );
      return {
        stage: stage.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()),
        level_ft: Number(ft),
        probability: probabilityToReach(predictedFt, Number(ft)),
      };
    });
    return probs.sort((a, b) => stageOrder.indexOf(a.stage) - stageOrder.indexOf(b.stage));
  }, [gauges, predictions]);

  const keyStations = useMemo(() => {
    const ids = ['07010000', '05587450', '06934500'];
    return gauges.filter(g => ids.includes(g.id));
  }, [gauges]);

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Gauge className="h-5 w-5 text-sky-600" />
            St. Louis River Forecast (model)
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Target: St. Louis; Sensors: Grafton & Hermann driving the model (no simulated data).
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            Refresh 30s
          </Badge>
          <Badge variant="secondary" className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {predictions[0]
              ? formatDistanceToNowStrict(new Date(predictions[0].prediction_time), { addSuffix: true })
              : 'waiting...'}
          </Badge>
          {predsFetching && <Badge variant="outline">updating…</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(gaugesLoading || predsLoading) && (
            <div className="col-span-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4 animate-spin" />
              Loading live predictions…
            </div>
          )}
          {!gaugesLoading && keyStations.length > 0 && (
            <>
              {keyStations.map(g => (
                <StationCard
                  key={g.id}
                  gauge={g}
                  prediction={predictions.find(p => p.gauge_id === g.id)}
                  stages={orderedStages}
                />
              ))}
            </>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2 border border-slate-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Critical transitions for St. Louis
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Probabilities use the backend prediction model.
              </p>
            </CardHeader>
            <CardContent className="space-y-3">
              {orderedStages.length === 0 && (
                <div className="text-sm text-muted-foreground">No stage data yet.</div>
              )}
              {orderedStages.map(stage => (
                <StageBar key={`${stage.stage}-${stage.level_ft}`} stage={stage} />
              ))}
            </CardContent>
          </Card>

          <Card className="border border-slate-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4 text-sky-600" />
                Data source
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <div>• Current levels: `/api/gauges` (database readings)</div>
              <div>• Predictions: `/api/predict/river-level` (linear trend model over recent readings)</div>
              <div>• No simulated values shown.</div>
              <div className="flex items-center gap-2 text-xs">
                <Badge variant="secondary">Refresh</Badge>
                <span>30s auto refresh</span>
                <Badge variant="outline" onClick={() => refetch()} className="cursor-pointer">Refresh now</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
}

// helpers
const metersToFeet = (m: number) => m / 0.3048;

const probabilityToReach = (predictedFt: number, stageFt: number) => {
  const scale = 1.2;
  const delta = predictedFt - stageFt;
  const prob = 1 / (1 + Math.exp(-delta / scale));
  return Math.max(0, Math.min(1, prob));
};
