import React from 'react';
import { X, ExternalLink, Calendar, Shield, Activity, TrendingUp } from 'lucide-react';

const DomainDetailModal = ({ domain, isOpen, onClose }) => {
  if (!isOpen || !domain) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const scorePercentage = Math.round((domain.opportunity_score || 0) * 100);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        {/* Backdrop */}
        <div
          className="fixed inset-0 transition-opacity bg-slate-900 bg-opacity-50"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative inline-block px-4 pt-5 pb-4 overflow-hidden text-left align-bottom transition-all transform bg-white rounded-lg shadow-xl sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full sm:p-6">
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-500 focus:outline-none"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="w-full">
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-2xl font-bold text-slate-900">{domain.domain}</h3>
                <a
                  href={`https://${domain.domain}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-600 hover:text-indigo-700"
                >
                  <ExternalLink className="w-5 h-5" />
                </a>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    domain.tier === 'Gold'
                      ? 'bg-yellow-100 text-yellow-800'
                      : domain.tier === 'Silver'
                      ? 'bg-slate-100 text-slate-700'
                      : 'bg-orange-100 text-orange-800'
                  }`}
                >
                  {domain.tier}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    domain.is_available
                      ? 'bg-green-100 text-green-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  {domain.is_available ? 'Available' : 'Expiring Soon'}
                </span>
              </div>
            </div>

            {/* Opportunity Score */}
            <div className="mb-6 p-4 bg-indigo-50 rounded-lg border border-indigo-100">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Opportunity Score</span>
                <span className="text-2xl font-bold text-indigo-600">{scorePercentage}</span>
              </div>
              <div className="w-full bg-white rounded-full h-3">
                <div
                  className={`h-3 rounded-full ${
                    scorePercentage >= 70
                      ? 'bg-green-500'
                      : scorePercentage >= 50
                      ? 'bg-yellow-500'
                      : 'bg-orange-500'
                  }`}
                  style={{ width: `${scorePercentage}%` }}
                />
              </div>
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              {/* WHOIS Info */}
              <div className="col-span-2 p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-5 h-5 text-slate-600" />
                  <h4 className="font-semibold text-slate-900">WHOIS Information</h4>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-500">Registrar:</span>
                    <p className="font-medium text-slate-900">{domain.registrar || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Status:</span>
                    <p className="font-medium text-slate-900">{domain.whois_status || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Created:</span>
                    <p className="font-medium text-slate-900">{formatDate(domain.creation_date)}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Expires:</span>
                    <p className="font-medium text-slate-900">{formatDate(domain.expiration_date)}</p>
                  </div>
                </div>
              </div>

              {/* Wayback Machine */}
              <div className="col-span-2 p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="w-5 h-5 text-slate-600" />
                  <h4 className="font-semibold text-slate-900">Historical Data</h4>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-500">Total Snapshots:</span>
                    <p className="font-medium text-slate-900">
                      {domain.total_snapshots?.toLocaleString() || '0'}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Peak Year:</span>
                    <p className="font-medium text-slate-900">{domain.peak_activity_year || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">First Snapshot:</span>
                    <p className="font-medium text-slate-900">{formatDate(domain.first_snapshot_date)}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Last Snapshot:</span>
                    <p className="font-medium text-slate-900">{formatDate(domain.last_snapshot_date)}</p>
                  </div>
                  {domain.page_title && (
                    <div className="col-span-2">
                      <span className="text-slate-500">Page Title:</span>
                      <p className="font-medium text-slate-900">{domain.page_title}</p>
                    </div>
                  )}
                  {domain.meta_description && (
                    <div className="col-span-2">
                      <span className="text-slate-500">Description:</span>
                      <p className="font-medium text-slate-900 text-xs">{domain.meta_description}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* SEO Metrics */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-5 h-5 text-slate-600" />
                  <h4 className="font-semibold text-slate-900">SEO Metrics</h4>
                </div>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-slate-500">Domain Authority:</span>
                    <p className="font-medium text-slate-900">{domain.domain_authority || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Page Authority:</span>
                    <p className="font-medium text-slate-900">{domain.page_authority || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Linking Domains:</span>
                    <p className="font-medium text-slate-900">
                      {domain.linking_root_domains?.toLocaleString() || '0'}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Total Links:</span>
                    <p className="font-medium text-slate-900">
                      {domain.total_links?.toLocaleString() || '0'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Trademark Risk */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-5 h-5 text-slate-600" />
                  <h4 className="font-semibold text-slate-900">Trademark Risk</h4>
                </div>
                <div className="text-sm">
                  <div className="mb-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        domain.has_trademark_risk
                          ? 'bg-red-100 text-red-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {domain.has_trademark_risk ? 'Risk Detected' : 'Low Risk'}
                    </span>
                  </div>
                  {domain.trademark_details && (
                    <p className="text-slate-600 text-xs">{domain.trademark_details}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="flex gap-3 pt-4 border-t border-slate-200">
                <a
                    href={domain.registrar_check_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 inline-flex justify-center items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-lg hover:bg-indigo-700 transition-colors"
                >
                    Check & Buy
                    <ExternalLink className="w-4 h-4" />
                </a>
                <a
                    href={`https://web.archive.org/web/*/${domain.domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 inline-flex justify-center items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors"
                >
                    View in Wayback Machine
                    <ExternalLink className="w-4 h-4" />
                </a>
                <button
                    onClick={onClose}
                    className="px-6 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                >
                    Close
                </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DomainDetailModal;
