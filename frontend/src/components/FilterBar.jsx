import React from 'react';
import { Filter } from 'lucide-react';

const FilterBar = ({ filters, setFilters }) => {
  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const toggleArrayFilter = (key, value) => {
    setFilters((prev) => ({
      ...prev,
      [key]: prev[key].includes(value)
        ? prev[key].filter((v) => v !== value)
        : [...prev[key], value],
    }));
  };

  return (
    <div className="p-6">
      <div className="flex items-center gap-2 mb-6">
        <Filter className="w-5 h-5 text-slate-600" />
        <h3 className="font-semibold text-slate-800">Filters</h3>
      </div>

      {/* Availability Status */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Availability
        </label>
        <div className="space-y-2">
          {['AVAILABLE', 'EXPIRING_SOON'].map((status) => (
            <label key={status} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.availability.includes(status)}
                onChange={() => toggleArrayFilter('availability', status)}
                className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700">
                {status === 'AVAILABLE' ? 'Available' : 'Expiring Soon'}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Tier */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Tier
        </label>
        <div className="space-y-2">
          {['PRIME', 'STRONG', 'DECENT'].map((tier) => (
            <label key={tier} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.tier.includes(tier)}
                onChange={() => toggleArrayFilter('tier', tier)}
                className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700">{tier}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Trademark Risk */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Trademark Risk
        </label>
        <div className="space-y-2">
          {['LOW', 'MEDIUM', 'HIGH'].map((risk) => (
            <label key={risk} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.trademarkRisk.includes(risk)}
                onChange={() => toggleArrayFilter('trademarkRisk', risk)}
                className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700">{risk}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Min Opportunity Score */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Min Opportunity Score: {filters.minOpportunityScore}
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={filters.minOpportunityScore}
          onChange={(e) => updateFilter('minOpportunityScore', parseInt(e.target.value))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        />
      </div>

      {/* Min Domain Authority */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Min Domain Authority: {filters.minDomainAuthority}
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={filters.minDomainAuthority}
          onChange={(e) => updateFilter('minDomainAuthority', parseInt(e.target.value))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        />
      </div>

      {/* Min Viral Score */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Min Viral Score: {filters.minViralScore}
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={filters.minViralScore}
          onChange={(e) => updateFilter('minViralScore', parseInt(e.target.value))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        />
      </div>

      {/* E-commerce Only */}
      <div className="mb-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.ecommerceOnly}
            onChange={(e) => updateFilter('ecommerceOnly', e.target.checked)}
            className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
          />
          <span className="text-sm font-medium text-slate-700">E-commerce Only</span>
        </label>
      </div>
    </div>
  );
};

export default FilterBar;
