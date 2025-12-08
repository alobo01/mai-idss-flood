import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Edit, Trash2, Eye } from 'lucide-react';
import type { Column } from '../DataTable';

interface TableRowComponentProps<T> {
  record: T;
  index: number;
  columns: Column<T>[];
  onView?: (record: T, index: number) => void;
  onEdit?: (record: T, index: number) => void;
  onDelete?: (record: T, index: number) => void;
  actions?: React.ReactNode;
}

export function TableRowComponent<T>({
  record,
  index,
  columns,
  onView,
  onEdit,
  onDelete,
  actions
}: TableRowComponentProps<T>) {
  const renderActions = () => {
    if (actions) {
      return actions;
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

  return (
    <Table>
      <TableBody>
        <TableRow>
          {columns.map((column) => (
            <TableCell
              key={String(column.key)}
              style={column.width ? { width: column.width } : undefined}
            >
              {column.render
                ? column.render(record[column.key], record, index)
                : String(record[column.key] || '')}
            </TableCell>
          ))}
          <TableCell className="w-[70px]">
            {renderActions()}
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}