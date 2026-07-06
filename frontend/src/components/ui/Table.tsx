import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface Column<T> {
  key: string;
  header: string;
  render?: (item: T, index: number) => ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey: (item: T, index: number) => string | number;
  onRowHover?: string;
}

export function Table<T>({ columns, data, rowKey }: TableProps<T>) {
  return (
    <div className="bg-anthro-surface rounded-2xl border border-anthro-border shadow-sm overflow-hidden">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-anthro-border">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  'py-4 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted',
                  col.className
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr
              key={rowKey(item, idx)}
              className="border-b border-anthro-bg hover:bg-anthro-bg transition-colors"
            >
              {columns.map((col) => (
                <td key={col.key} className={cn('py-5 px-6', col.className)}>
                  {col.render
                    ? col.render(item, idx)
                    : (item as Record<string, unknown>)[col.key] as ReactNode}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
