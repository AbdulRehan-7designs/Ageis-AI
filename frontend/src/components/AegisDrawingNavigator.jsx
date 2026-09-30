import React from 'react';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, LocateFixed } from 'lucide-react';

export default function AegisDrawingNavigator({ sheet = 1, onSheetChange }) {
  return (
    <div className="aegis-drawing-nav">
      <button className="aegis-mini-btn" onClick={() => onSheetChange && onSheetChange(Math.max(1, sheet - 1))}>
        <ChevronLeft size={14} />
      </button>
      <span>Sheet {sheet}</span>
      <button className="aegis-mini-btn" onClick={() => onSheetChange && onSheetChange(sheet + 1)}>
        <ChevronRight size={14} />
      </button>
      <div className="aegis-drawing-actions">
        <button className="aegis-mini-btn" aria-label="Zoom out"><ZoomOut size={14} /></button>
        <button className="aegis-mini-btn" aria-label="Zoom in"><ZoomIn size={14} /></button>
        <button className="aegis-mini-btn" aria-label="Focus evidence"><LocateFixed size={14} /></button>
      </div>
    </div>
  );
}
