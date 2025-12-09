import React from 'react';
import {
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableHeader,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import type { Column } from '../DataTable';

interface TableHeaderProps<T> {
  columns: Column<T>[];
  sortConfig?: {
    key: keyof T;
    direction: 'asc' | 'desc';
  } | null;
  onSort?: (key: keyof T) => void;
}

export function DataTableHeader<T>({
  columns,
  sortConfig,
  onSort
}: TableHeaderProps<T>) {
  const handleSort = (column: Column<T>) => {
    if (!column.sortable || !onSort) return;

    const currentDirection = sortConfig?.key === column.key ? sortConfig.direction : null;
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

    onSort(column.key);
  };

  const getSortIcon = (column: Column<T>) => {
    if (!column.sortable || !sortConfig || sortConfig.key !== column.key) {
      return null;
    }

    return (
      <span className="ml-1">
        {sortConfig.direction === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead
              key={String(column.key)}
              style={column.width ? { width: column.width } : undefined}
              className={cn(
                column.sortable && 'cursor-pointer hover:bg-muted/50',
                'font-medium'
              )}
              onClick={() => handleSort(column)}
            >
              <div className="flex items-center">
                {column.title}
                {getSortIcon(column)}
              </div>
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
    </Table>
  );
}