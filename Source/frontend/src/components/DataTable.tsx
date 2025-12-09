import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableRow, TableHeader } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Edit, Trash2, Eye, ArrowUpDown } from 'lucide-react';
import { TableFilters } from './table/TableFilters';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: keyof T;
  title: string;
  sortable?: boolean;
  searchable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  width?: string;
}

export interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  title?: string;
  description?: string;
  searchPlaceholder?: string;
  onAdd?: () => void;
  onEdit?: (record: T, index: number) => void;
  onDelete?: (record: T, index: number) => void;
  onView?: (record: T, index: number) => void;
  onExport?: () => void;
  onImport?: () => void;
  addButtonLabel?: string;
  className?: string;
  actions?: React.ReactNode;
  rowActions?: (record: T, index: number) => React.ReactNode;
  pageSize?: number;
  emptyMessage?: string;
}

export function DataTable<T>({
  data,
  columns,
  loading = false,
  title,
  searchPlaceholder = 'Search...',
  onAdd,
  onEdit,
  onDelete,
  onView,
  onExport,
  onImport,
  addButtonLabel = 'Add New',
  className,
  actions,
  rowActions,
  emptyMessage = 'No data available'
}: DataTableProps<T>) {
  const [searchValue, setSearchValue] = useState('');
  const [sortConfig, setSortConfig] = useState<{
    key: keyof T;
    direction: 'asc' | 'desc';
  } | null>(null);

  // Filter data based on search
  const filteredData = useMemo(() => {
    if (!searchValue) return data;

    return data.filter((record) => {
      return columns.some((column) => {
        if (!column.searchable) return false;

        const value = record[column.key];
        if (value === null || value === undefined) return false;

        return String(value).toLowerCase().includes(searchValue.toLowerCase());
      });
    });
  }, [data, searchValue, columns]);

  // Sort data based on sort config
  const sortedData = useMemo(() => {
    if (!sortConfig) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      const comparison = String(aValue).localeCompare(String(bValue));
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortConfig]);

  const handleSort = (key: keyof T) => {
    let direction: 'asc' | 'desc' = 'asc';

    if (sortConfig && sortConfig.key === key) {
      direction = sortConfig.direction === 'asc' ? 'desc' : 'asc';
    }

    setSortConfig({ key, direction });
  };

  const renderActions = (record: T, index: number) => {
    if (rowActions) {
      return rowActions(record, index);
    }

    if (!onView && !onEdit && !onDelete) {
      return null;
    }

    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {onView && (
            <DropdownMenuItem onClick={() => onView(record, index)}>
              <Eye className="mr-2 h-4 w-4" />
              View
            </DropdownMenuItem>
          )}
          {onEdit && (
            <>
              {onView && <DropdownMenuSeparator />}
              <DropdownMenuItem onClick={() => onEdit(record, index)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
            </>
          )}
          {onDelete && (
            <>
              {(onView || onEdit) && <DropdownMenuSeparator />}
              <DropdownMenuItem
                onClick={() => onDelete(record, index)}
                className="text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    );
  };

  const renderTableHeader = () => (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableCell
              key={String(column.key)}
              className={cn(
                'font-medium p-3 bg-muted/50',
                column.sortable && 'cursor-pointer hover:bg-muted/70'
              )}
              style={column.width ? { width: column.width } : undefined}
              onClick={() => column.sortable && handleSort(column.key)}
            >
              <div className="flex items-center">
                {column.title}
                {column.sortable && (
                  <span className="ml-1">
                    {sortConfig?.key === column.key ? (
                      sortConfig.direction === 'asc' ? '↑' : '↓'
                    ) : (
                      <ArrowUpDown className="h-3 w-3 text-muted-foreground" />
                    )}
                  </span>
                )}
              </div>
            </TableCell>
          ))}
          <TableCell className="w-[70px] font-medium p-3 bg-muted/50">
            Actions
          </TableCell>
        </TableRow>
      </TableHeader>
    </Table>
  );

  const renderTableBody = () => (
    <Table>
      <TableBody>
        {sortedData.map((record, index) => (
          <TableRow key={index} className="hover:bg-muted/50">
            {columns.map((column) => (
              <TableCell
                key={String(column.key)}
                className="p-3"
                style={column.width ? { width: column.width } : undefined}
              >
                {column.render
                  ? column.render(record[column.key], record, index)
                  : String(record[column.key] || '')}
              </TableCell>
            ))}
            <TableCell className="p-3 w-[70px]">
              {renderActions(record, index)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );

  return (
    <Card className={className}>
      {(title || onAdd || onExport || onImport) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          <TableFilters
            searchValue={searchValue}
            onSearchChange={setSearchValue}
            onExport={onExport}
            onImport={onImport}
            onAdd={onAdd}
            addButtonLabel={addButtonLabel}
            actions={actions}
          />
        </CardHeader>
      )}

      <CardContent className="p-0">
        {loading ? (
          <div className="p-8 text-center">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        ) : sortedData.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-muted-foreground">{emptyMessage}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            {renderTableHeader()}
            {renderTableBody()}
          </div>
        )}
      </CardContent>
    </Card>
  );
}