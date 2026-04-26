import React, { useState } from 'react';
import { X } from 'lucide-react';

const ScanConfigModal = ({ isOpen, onClose, onStart }) => {
  const [config, setConfig] = useState({
    sources: ['hackernews', 'producthunt'],
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onStart(config);
  };

  const toggleSource = (source) => {
    setConfig((prev) => ({
      ...prev,
      sources: prev.sources.includes(source)
        ? prev.sources.filter((s) => s !== source)
        : [...prev.sources, source],
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        {/* Backdrop */}
        <div
          className="fixed inset-0 transition-opacity bg-slate-900 bg-opacity-50"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative inline-block px-4 pt-5 pb-4 overflow-hidden text-left align-bottom transition-all transform bg-white rounded-lg shadow-xl sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-500 focus:outline-none"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="sm:flex sm:items-start">
            <div className="w-full mt-3 text-center sm:mt-0 sm:text-left">
              <h3 className="text-2xl font-bold leading-6 text-slate-900 mb-4">
                Configure New Scan
              </h3>
              <p className="text-sm text-slate-500 mb-6">
                Select the sources you want to scan for viral products from 2014-2019.
              </p>

              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-3">
                      Data Sources
                    </label>
                    <div className="space-y-3">
                      <label className="flex items-start gap-3 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                        <input
                          type="checkbox"
                          checked={config.sources.includes('hackernews')}
                          onChange={() => toggleSource('hackernews')}
                          className="mt-1 w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-slate-900">Hacker News</div>
                          <div className="text-sm text-slate-500">
                            Scan "Show HN" posts for product launches and domains
                          </div>
                        </div>
                      </label>

                      <label className="flex items-start gap-3 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                        <input
                          type="checkbox"
                          checked={config.sources.includes('producthunt')}
                          onChange={() => toggleSource('producthunt')}
                          className="mt-1 w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-slate-900">Product Hunt</div>
                          <div className="text-sm text-slate-500">
                            Scan Product Hunt launches for featured products
                          </div>
                        </div>
                      </label>

                      <label className="flex items-start gap-3 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                        <input
                          type="checkbox"
                          checked={config.sources.includes('youtube')}
                          onChange={() => toggleSource('youtube')}
                          className="mt-1 w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-slate-900">YouTube</div>
                          <div className="text-sm text-slate-500">
                            Scan viral product unboxings and reviews from 2014-2018 for expired description links
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>

                  {config.sources.length === 0 && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        Please select at least one data source to continue.
                      </p>
                    </div>
                  )}
                </div>

                <div className="mt-6 sm:mt-8 sm:flex sm:flex-row-reverse gap-3">
                  <button
                    type="submit"
                    disabled={config.sources.length === 0}
                    className="inline-flex justify-center w-full px-6 py-3 text-base font-medium text-white bg-indigo-600 border border-transparent rounded-lg shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Start Scan
                  </button>
                  <button
                    type="button"
                    onClick={onClose}
                    className="inline-flex justify-center w-full px-6 py-3 mt-3 text-base font-medium text-slate-700 bg-white border border-slate-300 rounded-lg shadow-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanConfigModal;
