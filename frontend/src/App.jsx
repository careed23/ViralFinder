import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, Activity, Download, LayoutDashboard, Settings } from 'lucide-react';
import api from './api/client';
import DomainTable from './components/DomainTable';
import FilterBar from './components/FilterBar';
import DomainDetailModal from './components/DomainDetailModal';
import ScanConfigModal from './components/ScanConfigModal';
import ExportButton from './components/ExportButton';

const App = () => {
  const [currentJobId, setCurrentJobId] = useState(localStorage.getItem('currentJobId') || null);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [isScanConfigOpen, setIsScanConfigOpen] = useState(false);
  const [filters, setFilters] = useState({
    availability: ['AVAILABLE', 'EXPIRING_SOON'],
    tier: ['PRIME', 'STRONG', 'DECENT'],
    trademarkRisk: ['LOW', 'MEDIUM'],
    minOpportunityScore: 40,
    minDomainAuthority: 0,
    minViralScore: 0,
    ecommerceOnly: false,
    sortBy: 'opportunity_score',
    sortOrder: 'desc'
  });

  const queryClient = useQueryClient();

  // Poll job status
  const { data: jobStatus } = useQuery({
    queryKey: ['jobStatus', currentJobId],
    queryFn: () => api.getScanStatus(currentJobId).then(res => res.data),
    enabled: !!currentJobId && currentJobId !== 'demo',
    refetchInterval: (data) => (data?.status === 'running' || data?.status === 'pending') ? 3000 : false,
  });

  // Fetch results
  const { data: resultsData, isLoading: isLoadingResults } = useQuery({
    queryKey: ['scanResults', currentJobId, filters],
    queryFn: () => api.getScanResults(currentJobId, {
      ...filters,
      tier: filters.tier.join(','),
      page_size: 100 // High limit for client-side table features
    }).then(res => res.data),
    enabled: !!currentJobId && (jobStatus?.status === 'complete' || currentJobId === 'demo'),
  });

  useEffect(() => {
    if (currentJobId) {
      localStorage.setItem('currentJobId', currentJobId);
    }
  }, [currentJobId]);

  const handleStartScan = async (config) => {
    try {
      const response = await api.startScan(config);
      setCurrentJobId(response.data.job_id);
      setIsScanConfigOpen(false);
      queryClient.invalidateQueries(['jobStatus', response.data.job_id]);
    } catch (error) {
      console.error('Failed to start scan:', error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 font-sans">
      {/* Top Navigation */}
      <header className="h-16 border-b bg-white flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center">
            <Search className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">ViralFinder</h1>
        </div>

        <div className="flex items-center gap-4">
          {jobStatus && jobStatus.status === 'running' && (
            <div className="flex items-center gap-3 px-4 py-1.5 bg-indigo-50 border border-indigo-100 rounded-full">
              <Activity className="w-4 h-4 text-indigo-600 animate-pulse" />
              <span className="text-sm font-medium text-indigo-700">
                {jobStatus.current_phase}: {jobStatus.progress_percent}%
              </span>
            </div>
          )}
          <button 
            onClick={() => setIsScanConfigOpen(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Scan
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Filters */}
        <aside className="w-72 border-r bg-white overflow-y-auto hidden lg:block">
          <FilterBar filters={filters} setFilters={setFilters} />
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {!currentJobId ? (
            <div className="flex-1 flex flex-center flex-col items-center justify-center p-12 text-center">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-6">
                <LayoutDashboard className="w-10 h-10 text-slate-400" />
              </div>
              <h2 className="text-2xl font-semibold text-slate-800 mb-2">No Active Scan</h2>
              <p className="text-slate-500 max-w-md mb-8">
                Start a new scan to discover expired domains from viral products between 2014 and 2019.
              </p>
              <button 
                onClick={() => setIsScanConfigOpen(true)}
                className="bg-indigo-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all"
              >
                Launch First Scan
              </button>
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-6 pb-0 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-slate-800">Scan Results</h2>
                  <p className="text-slate-500 text-sm">
                    Showing {resultsData?.total || 0} potential opportunities found
                  </p>
                </div>
                <div className="flex gap-2">
                  <ExportButton jobId={currentJobId} />
                </div>
              </div>
              <div className="flex-1 p-6 overflow-hidden">
                <DomainTable 
                  data={resultsData?.results || []} 
                  isLoading={isLoadingResults || jobStatus?.status === 'running'} 
                  onRowClick={setSelectedDomain}
                />
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Modals */}
      <ScanConfigModal 
        isOpen={isScanConfigOpen} 
        onClose={() => setIsScanConfigOpen(false)} 
        onStart={handleStartScan}
      />
      
      {selectedDomain && (
        <DomainDetailModal 
          domain={selectedDomain} 
          isOpen={!!selectedDomain} 
          onClose={() => setSelectedDomain(null)} 
        />
      )}
    </div>
  );
};

export default App;
