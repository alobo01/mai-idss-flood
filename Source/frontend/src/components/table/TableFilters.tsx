import React from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Search, Download, Upload, MoreHorizontal } from 'lucide-react';

interface TableFiltersProps<T> {
  searchValue: string;
  onSearchChange: (value: string) => void;
  onExport?: () => void;
  onImport?: () => void;
  onAdd?: () => void;
  addButtonLabel?: string;
  actions?: React.ReactNode;
}

export function TableFilters<T>({
  searchValue,
  onSearchChange,
  onExport,
  onImport,
  onAdd,
  addButtonLabel = 'Add New',
  actions
}: TableFiltersProps<T>) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-8 w-[250px]"
          />
        </div>
      </div>

      <div className="flex items-center space-x-2">
        {actions}

        {(onExport || onImport) && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onExport && (
                <>
                  <DropdownMenuItem onClick={onExport}>
                    <Download className="mr-2 h-4 w-4" />
                    Export
                  </DropdownMenuItem>
                </>
              )}
              {onImport && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={onImport}>
                    <Upload className="mr-2 h-4 w-4" />
                    Import
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {onAdd && (
          <Button onClick={onAdd} size="sm">
            Add New
          </Button>
        )}
      </div>
    </div>
  );
}