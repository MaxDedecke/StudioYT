import React from 'react';
import { Plus, Cloud, Folder, Info, Music2 } from 'lucide-react';
import { openExplorerFolder } from '../api';

interface NavbarProps {
  onOpenUpload: () => void;
  onOpenSettings: () => void;
  onOpenWorkflow: () => void;
  projectCount: number;
  activeRenderCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenUpload,
  onOpenSettings,
  onOpenWorkflow,
  projectCount,
  activeRenderCount,
}) => {
  return (
    <header className="border-b border-white/[0.08] bg-[#0c0d14]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Music2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-wider bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                FLYT STUDIO
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 uppercase tracking-widest">
                prodbyJMD
              </span>
            </div>
            <div className="text-[11px] text-zinc-500 font-medium">
              {projectCount} Beats in Pipeline {activeRenderCount > 0 && <span className="text-amber-400 font-semibold">· {activeRenderCount} rendert</span>}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-purple-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <Plus className="w-4 h-4" />
            <span>Beat hochladen</span>
          </button>

          <button
            onClick={onOpenWorkflow}
            title="Workflow Übersicht"
            className="p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] text-zinc-400 hover:text-white transition-colors"
          >
            <Info className="w-4 h-4" />
          </button>

          <button
            onClick={onOpenSettings}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] text-zinc-300 hover:text-white text-xs font-medium transition-colors"
          >
            <Cloud className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Drive & API</span>
          </button>

          <button
            onClick={() => openExplorerFolder('')}
            title="Beats Ordner im Explorer öffnen"
            className="p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] text-zinc-400 hover:text-white transition-colors"
          >
            <Folder className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
