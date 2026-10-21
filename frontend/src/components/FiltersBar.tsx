import React from 'react';
import { Search, Filter, SlidersHorizontal, CheckCircle2 } from 'lucide-react';

interface FiltersBarProps {
  search: string;
  onSearchChange: (val: string) => void;
  selectedKey: string;
  onKeyChange: (val: string) => void;
  sortBy: string;
  onSortChange: (val: string) => void;
  showCompleted: boolean;
  onToggleCompleted: () => void;
  availableKeys: string[];
}

export const FiltersBar: React.FC<FiltersBarProps> = ({
  search,
  onSearchChange,
  selectedKey,
  onKeyChange,
  sortBy,
  onSortChange,
  showCompleted,
  onToggleCompleted,
  availableKeys,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 mb-6 bg-white/[0.02] border border-white/[0.05] p-2.5 rounded-xl">
      {/* Search Bar */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Beats durchsuchen (z. B. back21, Drake, 140 BPM)..."
          className="w-full bg-[#12131b] border border-white/[0.08] focus:border-purple-500/50 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 outline-none transition-colors"
        />
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {/* Key Filter */}
        <div className="flex items-center gap-1.5 bg-[#12131b] border border-white/[0.08] rounded-lg px-2.5 py-1.5">
          <Filter className="w-3.5 h-3.5 text-zinc-400" />
          <select
            value={selectedKey}
            onChange={(e) => onKeyChange(e.target.value)}
            className="bg-transparent text-xs text-zinc-200 outline-none cursor-pointer"
          >
            <option value="" className="bg-[#12131b]">Alle Tonarten</option>
            {availableKeys.map((k) => (
              <option key={k} value={k} className="bg-[#12131b]">{k}</option>
            ))}
          </select>
        </div>

        {/* Sort By */}
        <div className="flex items-center gap-1.5 bg-[#12131b] border border-white/[0.08] rounded-lg px-2.5 py-1.5">
          <SlidersHorizontal className="w-3.5 h-3.5 text-zinc-400" />
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value)}
            className="bg-transparent text-xs text-zinc-200 outline-none cursor-pointer"
          >
            <option value="recent" className="bg-[#12131b]">Neueste zuerst</option>
            <option value="bpm_desc" className="bg-[#12131b]">BPM (High → Low)</option>
            <option value="bpm_asc" className="bg-[#12131b]">BPM (Low → High)</option>
            <option value="name" className="bg-[#12131b]">Name (A-Z)</option>
          </select>
        </div>

        {/* Completed Toggle */}
        <button
          onClick={onToggleCompleted}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
            showCompleted
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-[#12131b] border-white/[0.08] text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Archiv</span>
        </button>
      </div>
    </div>
  );
};
