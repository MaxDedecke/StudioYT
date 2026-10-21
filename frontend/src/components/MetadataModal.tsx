import React, { useState, useEffect } from 'react';
import { X, Copy, ExternalLink, RefreshCw, Save } from 'lucide-react';
import type { Project } from '../types';
import { regenerateMetadata, saveMetadata } from '../api';

interface MetadataModalProps {
  project: Project | null;
  onClose: () => void;
  showToast: (msg: string) => void;
  onMetadataUpdated: (newText: string) => void;
}

export const MetadataModal: React.FC<MetadataModalProps> = ({
  project,
  onClose,
  showToast,
  onMetadataUpdated,
}) => {
  const [content, setContent] = useState(project?.metadata_text || '');
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (project) {
      setContent(project.metadata_text || '');
    }
  }, [project]);

  if (!project) return null;

  const handleCopyAll = async () => {
    try {
      await navigator.clipboard.writeText(content);
      showToast('Alle Texte in Zwischenablage kopiert');
    } catch (e) {
      console.error(e);
    }
  };

  const handleCopyReelCaption = async () => {
    try {
      const match = content.match(/## 📱 Instagram Reel[\s\S]*?```(?:text)?\s*([\s\S]*?)```/);
      if (match && match[1]) {
        await navigator.clipboard.writeText(match[1].trim());
        showToast('IG Reel Caption kopiert');
      } else {
        await navigator.clipboard.writeText(content);
        showToast('Texte kopiert');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCopyTags = async () => {
    try {
      const match = content.match(/## 🏷️ YouTube Studio Tags[\s\S]*?\n([\s\S]*?)$/);
      if (match && match[1]) {
        await navigator.clipboard.writeText(match[1].trim());
        showToast('YouTube SEO Tags kopiert');
      } else {
        showToast('Keine Tags gefunden');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRegenerate = async () => {
    setLoading(true);
    try {
      const res = await regenerateMetadata(project.name);
      setContent(res.metadata_text);
      onMetadataUpdated(res.metadata_text);
      showToast('Neue KI-Titel & Texte generiert');
    } catch (e: any) {
      alert(e.message || 'Fehler beim Neugenerieren');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await saveMetadata(project.name, content);
      onMetadataUpdated(content);
      setIsEditing(false);
      showToast('Metadaten gespeichert');
    } catch (e: any) {
      alert(e.message || 'Fehler beim Speichern');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#12131b] border border-white/[0.1] rounded-2xl w-full max-w-3xl max-h-[92vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div>
            <h2 className="text-base font-extrabold text-white">YouTube & Instagram Release Suite</h2>
            <div className="text-xs text-zinc-400 mt-0.5">Projekt: {project.name.toUpperCase()} · BPM: {project.bpm} · {project.key}</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRegenerate}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs font-semibold text-zinc-300 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>↻ Neu generieren</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-zinc-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Box */}
        <div className="relative">
          {isEditing ? (
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={16}
              className="w-full bg-[#090a0f] border border-white/[0.12] rounded-xl p-4 text-xs font-mono text-zinc-200 outline-none focus:border-purple-500/50 leading-relaxed"
            />
          ) : (
            <pre className="w-full bg-[#090a0f] border border-white/[0.08] rounded-xl p-4 text-xs font-mono text-zinc-300 overflow-x-auto max-h-[50vh] whitespace-pre-wrap leading-relaxed select-text">
              {content || 'Keine Metadaten vorhanden. Klicke auf "Neu generieren".'}
            </pre>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between border-t border-white/[0.08] pt-3 flex-wrap gap-2">
          {/* External links */}
          <div className="flex items-center gap-2">
            <a
              href="https://studio.youtube.com/channel/upload"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 font-medium"
            >
              <span>YouTube Studio</span>
              <ExternalLink className="w-3.5 h-3.5 text-zinc-500" />
            </a>
            <a
              href="https://www.instagram.com/"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 font-medium"
            >
              <span>Instagram</span>
              <ExternalLink className="w-3.5 h-3.5 text-zinc-500" />
            </a>
          </div>

          {/* Copy helpers */}
          <div className="flex items-center gap-2">
            {isEditing ? (
              <button
                onClick={handleSave}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-md shadow-emerald-500/20"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Speichern</span>
              </button>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 font-medium"
              >
                <span>Bearbeiten</span>
              </button>
            )}

            <button
              onClick={handleCopyTags}
              className="px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 font-medium"
            >
              SEO Tags
            </button>

            <button
              onClick={handleCopyReelCaption}
              className="px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 font-medium"
            >
              IG Reel Caption
            </button>

            <button
              onClick={handleCopyAll}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-xs font-semibold text-white shadow-md shadow-purple-500/20"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Alles kopieren</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
