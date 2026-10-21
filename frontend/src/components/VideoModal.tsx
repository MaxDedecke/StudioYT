import React, { useState } from 'react';
import { X, Download, Folder, RefreshCw, Scissors } from 'lucide-react';
import type { Project } from '../types';
import { triggerRender, openExplorerFolder } from '../api';

interface VideoModalProps {
  project: Project | null;
  videoType: 'main' | 'short';
  onClose: () => void;
  showToast: (msg: string) => void;
  onRenderStarted: () => void;
}

export const VideoModal: React.FC<VideoModalProps> = ({
  project,
  videoType,
  onClose,
  showToast,
  onRenderStarted,
}) => {
  const [currentType, setCurrentType] = useState<'main' | 'short'>(videoType);
  const [shortStart, setShortStart] = useState<number>(12);
  const [shortDur, setShortDur] = useState<number>(30);
  const [rendering, setRendering] = useState(false);

  if (!project) return null;

  const videoFilename = currentType === 'main' ? 'final_youtube_video.mp4' : 'short_reel_video.mp4';
  const videoUrl = `/projects/${project.name}/${videoFilename}?t=${project.updated_at || 0}`;

  const handleReRenderShort = async () => {
    setRendering(true);
    try {
      await triggerRender(project.name, 'short_only', shortStart, shortDur);
      showToast('Rendering für Short/Reel gestartet...');
      onRenderStarted();
      onClose();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Starten des Renderings');
    } finally {
      setRendering(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#12131b] border border-white/[0.1] rounded-2xl w-full max-w-3xl max-h-[92vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-4">
        {/* Header with Type Selector */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-extrabold text-white">Video Vorschau · {project.name.toUpperCase()}</h2>
            <div className="flex bg-[#090a0f] border border-white/[0.08] p-0.5 rounded-lg ml-3">
              <button
                onClick={() => setCurrentType('main')}
                className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                  currentType === 'main' ? 'bg-purple-600 text-white shadow' : 'text-zinc-400 hover:text-white'
                }`}
              >
                1440p Widescreen (16:9)
              </button>
              <button
                onClick={() => setCurrentType('short')}
                className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                  currentType === 'short' ? 'bg-purple-600 text-white shadow' : 'text-zinc-400 hover:text-white'
                }`}
              >
                Short / Reel (9:16)
              </button>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-zinc-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video Player */}
        <div className="flex items-center justify-center bg-black rounded-xl overflow-hidden border border-white/[0.08] p-2 min-h-[340px] max-h-[58vh]">
          <video
            key={videoUrl}
            src={videoUrl}
            controls
            playsInline
            autoPlay
            className={`rounded-lg ${currentType === 'short' ? 'max-h-[54vh] aspect-[9/16]' : 'w-full max-h-[54vh] aspect-video'}`}
          />
        </div>

        {/* Short / Reel Custom Recut Panel */}
        {currentType === 'short' && (
          <div className="bg-[#0b0c13] border border-purple-500/20 rounded-xl p-3.5">
            <div className="text-xs font-bold text-purple-300 flex items-center gap-1.5 mb-2.5">
              <Scissors className="w-3.5 h-3.5" />
              <span>Short / Instagram Reel Schnittpunkt & Dauer anpassen:</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
              <div>
                <label className="text-[11px] text-zinc-400 font-medium block mb-1">Startpunkt im Beat:</label>
                <select
                  value={shortStart}
                  onChange={(e) => setShortStart(Number(e.target.value))}
                  className="w-full bg-[#141520] border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white outline-none cursor-pointer"
                >
                  <option value={0}>Ab 0:00 (Intro)</option>
                  <option value={12}>Ab 0:12 (Drop / Hook)</option>
                  <option value={15}>Ab 0:15 (Hook)</option>
                  <option value={30}>Ab 0:30 (Part / Verse)</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] text-zinc-400 font-medium block mb-1">Dauer des Clips:</label>
                <select
                  value={shortDur}
                  onChange={(e) => setShortDur(Number(e.target.value))}
                  className="w-full bg-[#141520] border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white outline-none cursor-pointer"
                >
                  <option value={30}>30 Sekunden</option>
                  <option value={45}>45 Sekunden</option>
                  <option value={58}>58 Sekunden (Max Short)</option>
                </select>
              </div>
              <button
                onClick={handleReRenderShort}
                disabled={rendering}
                className="w-full py-1.5 px-3 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${rendering ? 'animate-spin' : ''}`} />
                <span>Neu rendern</span>
              </button>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-white/[0.08] pt-3 flex-wrap gap-2">
          <button
            onClick={() => openExplorerFolder(project.name)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300"
          >
            <Folder className="w-4 h-4" />
            <span>Im Explorer zeigen</span>
          </button>
          <a
            href={videoUrl}
            download={videoFilename}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-xs font-semibold text-white shadow-md shadow-purple-500/20"
          >
            <Download className="w-4 h-4" />
            <span>MP4 Video herunterladen</span>
          </a>
        </div>
      </div>
    </div>
  );
};
