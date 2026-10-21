import React from 'react';
import { X, Sparkles, Video, Cloud } from 'lucide-react';

interface WorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const WorkflowModal: React.FC<WorkflowModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const steps = [
    {
      num: '1',
      title: 'Beat ablegen (MP3)',
      desc: 'Zieh deinen FL Studio / DAW MP3-Export rein. FLYT analysiert BPM, Key, Timestamps und generiert ein einzigartiges Lithen Green-Night Artwork.',
      icon: <Sparkles className="w-4 h-4 text-purple-400" />,
    },
    {
      num: '2',
      title: 'Gemini Video-Loop',
      desc: '1-Klick auf "Gemini öffnen" kopiert den optimierten Prompt in die Zwischenablage. Lade die animierte MP4 herunter und zieh sie in FLYT.',
      icon: <Video className="w-4 h-4 text-cyan-400" />,
    },
    {
      num: '3',
      title: '1440p Video & 9:16 Short',
      desc: 'Die FFmpeg Pipeline rendert automatisch das 1440p YouTube Hauptvideo und einen 9:16 Short / Reel mit animierter Typografie.',
      icon: <Video className="w-4 h-4 text-emerald-400" />,
    },
    {
      num: '4',
      title: 'YouTube Thumbnail Studio',
      desc: 'Generiere 4 klickstarke 16:9 Thumbnails im visuellen Stil des Artists mit 1-Klick Vorschau wie im YouTube-Feed.',
      icon: <Sparkles className="w-4 h-4 text-amber-400" />,
    },
    {
      num: '5',
      title: 'Release & Google Drive',
      desc: 'Kopiere Titel, Beschreibung, SEO Tags und Reel Caption mit 1 Klick. Alle Dateien werden automatisch in Google Drive gesichert.',
      icon: <Cloud className="w-4 h-4 text-blue-400" />,
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#12131b] border border-white/[0.1] rounded-2xl w-full max-w-lg p-6 shadow-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <h2 className="text-base font-extrabold text-white">Der FLYT Producer Workflow</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-zinc-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-col gap-3.5 my-2">
          {steps.map((s) => (
            <div key={s.num} className="flex items-start gap-3 bg-[#090a0f] border border-white/[0.05] p-3 rounded-xl">
              <div className="w-7 h-7 rounded-lg bg-white/[0.05] border border-white/[0.08] flex items-center justify-center flex-shrink-0 mt-0.5">
                {s.icon}
              </div>
              <div>
                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span className="text-purple-400">#{s.num}</span> {s.title}
                </div>
                <div className="text-[11px] text-zinc-400 mt-0.5 leading-relaxed">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-white/[0.08] pt-3 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-white/[0.08] hover:bg-white/[0.15] text-xs font-semibold text-white"
          >
            Verstanden
          </button>
        </div>
      </div>
    </div>
  );
};
