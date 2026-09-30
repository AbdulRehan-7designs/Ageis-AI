import React from 'react';
import { FileText, Bot, ArrowUpDown } from 'lucide-react';

const defaultFilters = [
  { id: 'all', label: 'All Sources' },
  { id: 'documents', label: 'Documents' },
  { id: 'drawings', label: 'Drawings' },
];

export default function AegisDocFilterBar({
  totalDocs = 0,
  activeModel,
  filterOptions = defaultFilters,
  activeFilter = 'all',
  onFilterChange,
}) {
  const options = filterOptions.length ? filterOptions : defaultFilters;

  return (
    <div className="aegis-filter-bar">
      <div className="aegis-filter-group">
        {options.map((filter) => (
          <button
            key={filter.id}
            className={`aegis-filter-pill ${activeFilter === filter.id ? 'active' : ''}`}
            onClick={() => onFilterChange && onFilterChange(filter.id)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      <div className="aegis-filter-meta">
        <div className="aegis-meta-chip">
          <FileText size={14} />
          <span>{totalDocs} {totalDocs === 1 ? 'source' : 'sources'}</span>
        </div>
        <div className="aegis-meta-chip subtle">
          <Bot size={14} />
          <span>{activeModel && activeModel !== 'auto' ? activeModel : 'Model: Auto-routed'}</span>
        </div>
        <div className="aegis-meta-chip subtle">
          <ArrowUpDown size={14} />
          <span>Sources available</span>
        </div>
      </div>
    </div>
  );
}
