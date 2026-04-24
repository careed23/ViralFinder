import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
} from '@tanstack/react-table';
import { ArrowUpDown, ExternalLink } from 'lucide-react';

const DomainTable = ({ data, isLoading, onRowClick }) => {
  const columns = useMemo(
    () => [
      {
        accessorKey: 'domain',
        header: 'Domain',
        cell: ({ getValue }) => (
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-900">{getValue()}</span>
            <a
              href={`https://${getValue()}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-indigo-600"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        ),
      },
      {
        accessorKey: 'opportunity_score',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-1 hover:text-indigo-600"
          >
            Score
            <ArrowUpDown className="w-3 h-3" />
          </button>
        ),
        cell: ({ getValue }) => {
          const score = getValue();
          const percentage = Math.round((score || 0) * 100);
          return (
            <div className="flex items-center gap-2">
              <div className="w-16 bg-slate-100 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    percentage >= 70
                      ? 'bg-green-500'
                      : percentage >= 50
                      ? 'bg-yellow-500'
                      : 'bg-orange-500'
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="text-sm font-medium text-slate-700">{percentage}</span>
            </div>
          );
        },
      },
      {
        accessorKey: 'tier',
        header: 'Tier',
        cell: ({ getValue }) => {
          const tier = getValue();
          const colors = {
            Gold: 'bg-yellow-100 text-yellow-800 border-yellow-200',
            Silver: 'bg-slate-100 text-slate-700 border-slate-200',
            Bronze: 'bg-orange-100 text-orange-800 border-orange-200',
          };
          return (
            <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${colors[tier] || ''}`}>
              {tier}
            </span>
          );
        },
      },
      {
        accessorKey: 'expiry_status',
        header: 'Status',
        cell: ({ getValue }) => {
          const status = getValue();
          const isAvailable = status === 'AVAILABLE';
          return (
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium ${
                isAvailable
                  ? 'bg-green-100 text-green-800'
                  : 'bg-blue-100 text-blue-800'
              }`}
            >
              {isAvailable ? 'Available' : 'Expiring Soon'}
            </span>
          );
        },
      },
      {
        accessorKey: 'domain_authority',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-1 hover:text-indigo-600"
          >
            DA
            <ArrowUpDown className="w-3 h-3" />
          </button>
        ),
        cell: ({ getValue }) => (
          <span className="text-sm text-slate-700">{getValue() || 'N/A'}</span>
        ),
      },
      {
        accessorKey: 'total_snapshots',
        header: 'Snapshots',
        cell: ({ getValue }) => (
          <span className="text-sm text-slate-700">{getValue()?.toLocaleString() || 0}</span>
        ),
      },
      {
        accessorKey: 'page_title',
        header: 'Title',
        cell: ({ getValue }) => (
          <span className="text-sm text-slate-600 truncate max-w-xs block">
            {getValue() || 'N/A'}
          </span>
        ),
      },
    ],
    []
  );

  const table = useReactTable({
    data: data || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    initialState: {
      sorting: [{ id: 'opportunity_score', desc: true }],
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No domains found matching your filters.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-100">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => onRowClick(row.original)}
                className="hover:bg-indigo-50 cursor-pointer transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3 text-sm">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DomainTable;
