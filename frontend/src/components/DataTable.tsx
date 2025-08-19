import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';

interface Props {
  data: any[];
  maxRows?: number;
}

const DataTable: React.FC<Props> = ({ data, maxRows = 10 }) => {
  const [showAll, setShowAll] = useState(false);
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);

  // Sort data
  const sortedData = React.useMemo(() => {
    if (!data || data.length === 0) return [];
    if (!sortConfig) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }

      const aString = String(aValue).toLowerCase();
      const bString = String(bValue).toLowerCase();

      if (aString < bString) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aString > bString) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig]);

  if (!data || data.length === 0) {
    return null;
  }

  const columns = Object.keys(data[0]);

  const displayData = showAll ? sortedData : sortedData.slice(0, maxRows);

  const handleSort = (key: string) => {
    setSortConfig(current => ({
      key,
      direction: current?.key === key && current.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (typeof value === 'string' && value.includes('T') && value.includes(':')) {
      // Likely a date
      try {
        return new Date(value).toLocaleDateString();
      } catch {
        return value;
      }
    }
    return String(value);
  };

  const formatColumnName = (column: string): string => {
    return column
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const exportToCSV = () => {
    const headers = columns.join(',');
    const rows = sortedData.map(row => 
      columns.map(col => {
        const value = row[col];
        if (value === null || value === undefined) return '';
        return `"${String(value).replace(/"/g, '""')}"`;
      }).join(',')
    );
    
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cricket_data.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">
          Results ({data.length} record{data.length !== 1 ? 's' : ''})
        </h3>
        <button
          onClick={exportToCSV}
          className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
        >
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  className="cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{formatColumnName(column)}</span>
                    {sortConfig?.key === column && (
                      sortConfig.direction === 'asc' 
                        ? <ChevronUp className="w-3 h-3" />
                        : <ChevronDown className="w-3 h-3" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column} className="font-mono text-xs">
                    {formatValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Show more/less button */}
      {data.length > maxRows && (
        <div className="px-4 py-3 border-t border-gray-200 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {showAll 
              ? `Show less (showing ${displayData.length}/${data.length})`
              : `Show all ${data.length} rows`
            }
          </button>
        </div>
      )}
    </div>
  );
};

export default DataTable;