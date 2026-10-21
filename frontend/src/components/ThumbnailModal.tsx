import React, { useState, useEffect } from 'react';
import { X, Sparkles, Check, Download, Folder, Loader2 } from 'lucide-react';
import type { Project, ThumbnailState } from '../types';
import { getThumbnails, generateThumbnails, selectThumbnail, openExplorerFolder } from '../api';

interface ThumbnailModalProps {
  project: Project | null;
  onClose: () => void;
  showToast: (msg: string) => void;
  onThumbnailSelected: () => void;
}

export const ThumbnailModal: React.FC<ThumbnailModalProps> = ({
  project,
  onClose,
  showToast,
  onThumbnailSelected,
}) => {
  const [state, setState] = useState<ThumbnailState | null>(null);
  const [artistInput, setArtistInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    if (!project) return;
    loadState(true);
  }, [project]);

  const loadState = async (initial = false) => {
    if (!project) return;
    try {
      const data = await getThumbnails(project.name);
      setState(data);
      if (initial && data.default_artist) {
        setArtistInput(data.default_artist);
      }
      if (data.job && data.job.active) {
        setPolling(true);
      } else {
        setPolling(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    let timer: any = null;
    if (polling && project) {
      timer = setTimeout(() => {
        loadState(false);
      }, 1500);
    }
    return () => clearTimeout(timer);
  }, [polling, state]);

  if (!project) return null;

  const handleGenerate = async () => {
    if (!project) return;
    setLoading(true);
    try {
      await generateThumbnails(project.name, artistInput.trim(), 4);
      showToast('Generierung gestartet...');
      setPolling(true);
      loadState(false);
    } catch (e: any) {
      alert(e.message || 'Fehler beim Starten');
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (file: string) => {
    if (!project) return;
    try {
      await selectThumbnail(project.name, file);
      showToast('Thumbnail ausgewählt (thumbnail.jpg)');
      onThumbnailSelected();
      loadState(false);
    } catch (e: any) {
      alert(e.message || 'Fehler beim Auswählen');
    }
  };

  const job = state?.job;
  const isJobActive = !!(job && job.active);
  const previewTitle = state?.titles && state.titles[0] ? state.titles[0] : `[FREE] ${artistInput || 'Type'} Type Beat - "${project.name.toUpperCase()}"`;
  const pendingPlaceholders = isJobActive ? Math.max(0, (job?.total || 4) - (job?.done || 0) - (job?.failed || 0)) : 0;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#12131b] border border-white/[0.1] rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
          <div>
            <h2 className="text-base font-extrabold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>YouTube Thumbnail Studio · {project.name.toUpperCase()}</span>
            </h2>
            <p className="text-xs text-zinc-400 mt-1">
              KI-Bild im visuellen Vibe des Artists (anonym, ohne Gesichter) · Zentriert 4:5 auf 16:9 Schwarzbalken (1280×720) · Maximale Klickrate.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-zinc-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Artist Chips (Fast Selection) */}
        {state?.artists && state.artists.length > 0 && (
          <div>
            <div className="text-[11px] font-semibold text-zinc-400 mb-1.5">Erkannte Artists (Klicken zum Übernehmen):</div>
            <div className="flex flex-wrap gap-1.5">
              {state.artists.map((a) => (
                <button
                  key={a}
                  onClick={() => setArtistInput(a)}
                  className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                    artistInput === a
                      ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300 font-semibold'
                      : 'bg-white/[0.04] border-white/[0.08] text-zinc-300 hover:border-white/20'
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input & Generate Trigger */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={artistInput}
            onChange={(e) => setArtistInput(e.target.value)}
            placeholder="Artist eingeben (z. B. Future x Drake, Metro Boomin, Don Toliver)..."
            className="flex-1 bg-[#090a0f] border border-white/[0.1] focus:border-cyan-500/50 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 outline-none"
          />
          <button
            onClick={handleGenerate}
            disabled={loading || isJobActive}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 flex items-center gap-2"
          >
            {isJobActive ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generiert...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>4 Thumbnails generieren</span>
              </>
            )}
          </button>
        </div>

        {/* Status text */}
        <div className="text-xs text-zinc-400 min-h-[16px]">
          {isJobActive ? (
            <span className="text-cyan-400 font-medium flex items-center gap-1.5">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {job?.label} ({job?.done}/{job?.total} fertig)
            </span>
          ) : job?.label ? (
            <span>{job.label}</span>
          ) : state?.variants.length === 0 ? (
            <span>Noch keine Thumbnails vorhanden. Wähle einen Artist und starte die Generierung.</span>
          ) : (
            <span>Klicke auf ein Thumbnail, um es als offizielles YouTube-Cover festzulegen.</span>
          )}
        </div>

        {/* 16:9 Feed Preview Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Shimmer placeholders while generating */}
          {Array.from({ length: pendingPlaceholders }).map((_, i) => (
            <div key={`pending-${i}`} className="p-2 rounded-xl bg-[#0b0c13] border border-white/[0.05] animate-pulse">
              <div className="aspect-video bg-zinc-800/50 rounded-lg flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
              </div>
              <div className="h-4 bg-zinc-800/50 rounded mt-3 w-3/4"></div>
              <div className="h-3 bg-zinc-800/30 rounded mt-1.5 w-1/2"></div>
            </div>
          ))}

          {/* Generated Thumbnails */}
          {state?.variants.map((v) => {
            const isSelected = state.selected_src === v;
            return (
              <div
                key={v}
                onClick={() => handleSelect(v)}
                className={`p-2.5 rounded-xl cursor-pointer transition-all duration-200 border-2 ${
                  isSelected
                    ? 'bg-emerald-500/10 border-emerald-500 shadow-lg shadow-emerald-500/10'
                    : 'bg-[#0d0e15] border-transparent hover:border-white/20'
                }`}
              >
                <div className="relative aspect-video rounded-lg overflow-hidden bg-black">
                  <img
                    src={`/projects/${project.name}/${v}`}
                    alt="Thumbnail"
                    className="w-full h-full object-cover"
                  />
                  {isSelected && (
                    <div className="absolute top-2 left-2 px-2 py-1 rounded bg-emerald-500 text-black text-[10px] font-extrabold flex items-center gap-1 shadow-md">
                      <Check className="w-3 h-3 stroke-[3]" />
                      <span>AUSGEWÄHLT</span>
                    </div>
                  )}
                  {project.duration_str && project.duration_str !== '--:--' && (
                    <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/80 text-white text-[10px] font-semibold">
                      {project.duration_str}
                    </div>
                  )}
                </div>

                {/* YouTube Feed Preview Typography */}
                <div className="mt-2.5">
                  <div className="text-xs font-semibold text-zinc-200 line-clamp-2 leading-snug">
                    {previewTitle}
                  </div>
                  <div className="text-[11px] text-zinc-500 mt-1">
                    prodbyJMD · Vorschau im YouTube-Feed
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-white/[0.08] pt-4 flex-wrap gap-2">
          <button
            onClick={() => openExplorerFolder(project.name)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300"
          >
            <Folder className="w-4 h-4" />
            <span>Im Explorer zeigen</span>
          </button>

          {state?.has_selected && (
            <a
              href={`/projects/${project.name}/thumbnail.jpg`}
              download={`${project.name}_thumbnail.jpg`}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-md shadow-emerald-500/20"
            >
              <Download className="w-4 h-4" />
              <span>Ausgewähltes Thumbnail speichern</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
