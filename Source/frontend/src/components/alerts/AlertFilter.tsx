import React from 'react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Filter, Bell, BellOff } from 'lucide-react';
import type { AlertSeverity } from '@/types';

interface AlertFilterProps {
  selectedSeverity: string;
  onSeverityChange: (severity: string) => void;
  onFilterToggle: () => void;
  isFilterOpen: boolean;
}

const severityOptions: { value: AlertSeverity | 'all'; label: string }[] = [
  { value: 'all', label: 'All Severities' },
  { value: 'Low', label: 'Low' },
  { value: 'Moderate', label: 'Moderate' },
  { value: 'High', label: 'High' },
  { value: 'Severe', label: 'Severe' },
];

export function AlertFilter({
  selectedSeverity,
  onSeverityChange,
  onFilterToggle,
  isFilterOpen
}: AlertFilterProps) {
  return (
    <div className="flex items-center gap-2">
      <Select value={selectedSeverity} onValueChange={onSeverityChange}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Filter by severity" />
        </SelectTrigger>
        <SelectContent>
          {severityOptions.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button
        variant="outline"
        size="sm"
        onClick={onFilterToggle}
        className="shrink-0"
      >
        <Filter className="h-4 w-4 mr-2" />
        Filters
      </Button>

      <Button
        variant="outline"
        size="sm"
        className="shrink-0"
      >
        {isFilterOpen ? (
          <>
            <BellOff className="h-4 w-4 mr-2" />
            Mute
          </>
        ) : (
          <>
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </>
        )}
      </Button>
    </div>
  );
}