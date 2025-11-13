import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Layers, Eye, EyeOff, Clock, MapPin, AlertTriangle } from 'lucide-react';
import type { TimeHorizon, MapLayer } from '@/types';

interface LayerControlsProps {
  layers: {
    zones: boolean;
    risk: boolean;
    assets: boolean;
    gauges: boolean;
    alerts: boolean;
  };
  onLayerToggle: (layer: keyof LayerControlsProps['layers']) => void;
  timeHorizon: TimeHorizon;
  onTimeHorizonChange: (horizon: TimeHorizon) => void;
  opacity: number;
  onOpacityChange: (opacity: number) => void;
}

const timeHorizonOptions: { value: TimeHorizon; label: string }[] = [
  { value: '6h', label: '6 hours' },
  { value: '12h', label: '12 hours' },
  { value: '24h', label: '1 day' },
  { value: '48h', label: '2 days' },
  { value: '72h', label: '3 days' },
];

export function LayerControls({
  layers,
  onLayerToggle,
  timeHorizon,
  onTimeHorizonChange,
  opacity,
  onOpacityChange,
}: LayerControlsProps) {
  return (
    <div className="absolute top-4 right-4 space-y-2 z-10">
      {/* Time Horizon Control */}
      <Card className="p-3 shadow-lg min-w-[200px]">
        <div className="flex items-center space-x-2 mb-2">
          <Clock className="h-4 w-4" />
          <span className="text-sm font-medium">Forecast Horizon</span>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="w-full justify-between">
              <span>{timeHorizonOptions.find(h => h.value === timeHorizon)?.label}</span>
              <Clock className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            {timeHorizonOptions.map((option) => (
              <DropdownMenuItem
                key={option.value}
                onClick={() => onTimeHorizonChange(option.value)}
                className={timeHorizon === option.value ? 'bg-accent' : ''}
              >
                {option.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </Card>

      {/* Layer Visibility Controls */}
      <Card className="p-3 shadow-lg min-w-[200px]">
        <div className="flex items-center space-x-2 mb-2">
          <Layers className="h-4 w-4" />
          <span className="text-sm font-medium">Map Layers</span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MapPin className="h-3 w-3" />
              <span className="text-xs">Zones</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onLayerToggle('zones')}
              className="h-6 w-6 p-0"
            >
              {layers.zones ? (
                <Eye className="h-3 w-3" />
              ) : (
                <EyeOff className="h-3 w-3" />
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-red-500" />
              <span className="text-xs">Risk Overlay</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onLayerToggle('risk')}
              className="h-6 w-6 p-0"
            >
              {layers.risk ? (
                <Eye className="h-3 w-3" />
              ) : (
                <EyeOff className="h-3 w-3" />
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-purple-500" />
              <span className="text-xs">Critical Assets</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onLayerToggle('assets')}
              className="h-6 w-6 p-0"
            >
              {layers.assets ? (
                <Eye className="h-3 w-3" />
              ) : (
                <EyeOff className="h-3 w-3" />
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-blue-500" />
              <span className="text-xs">River Gauges</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onLayerToggle('gauges')}
              className="h-6 w-6 p-0"
            >
              {layers.gauges ? (
                <Eye className="h-3 w-3" />
              ) : (
                <EyeOff className="h-3 w-3" />
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-3 w-3 text-orange-500" />
              <span className="text-xs">Alerts</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onLayerToggle('alerts')}
              className="h-6 w-6 p-0"
            >
              {layers.alerts ? (
                <Eye className="h-3 w-3" />
              ) : (
                <EyeOff className="h-3 w-3" />
              )}
            </Button>
          </div>
        </div>
      </Card>

      {/* Opacity Control */}
      <Card className="p-3 shadow-lg min-w-[200px]">
        <div className="text-sm font-medium mb-2">Layer Opacity</div>
        <input
          type="range"
          min="0"
          max="100"
          value={opacity * 100}
          onChange={(e) => onOpacityChange(parseInt(e.target.value) / 100)}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0%</span>
          <span>{Math.round(opacity * 100)}%</span>
          <span>100%</span>
        </div>
      </Card>
    </div>
  );
}