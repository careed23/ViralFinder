import React from 'react';
import { Download } from 'lucide-react';
import api from '../api/client';

const ExportButton = ({ jobId }) => {
  const handleExport = () => {
    window.open(api.exportResults(jobId), '_blank');
  };

  return (
    <button
      onClick={handleExport}
      className="flex items-center gap-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
    >
      <Download className="w-4 h-4" />
      Export
    </button>
  );
};

export default ExportButton;
