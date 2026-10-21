import React, { useState, useEffect } from 'react';
import { X, Cloud, ExternalLink, Save, RefreshCw } from 'lucide-react';
import type { AppConfig } from '../types';
import { getConfig, updateConfig, syncDrive } from '../api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  showToast: (msg: string) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  showToast,
}) => {
  const [config, setConfig] = useState<AppConfig>({
    gdrive_path: '',
    gemini_api_key: '',
    hf_api_key: '',
  });
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      load();
    }
  }, [isOpen]);

  const load = async () => {
    try {
      const data = await getConfig();
      setConfig(data);
    } catch (e) {
      console.error(e);
    }
  };

  if (!isOpen) return null;

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateConfig(config);
      showToast('Einstellungen gespeichert');
      onClose();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Speichern');
    } finally {
      setSaving(false);
    }
  };

  const handleSyncAll = async () => {
    setSyncing(true);
    try {
      const res = await syncDrive();
      showToast(`Alle Beats mit Google Drive synchronisiert (${res.result?.length || 0} Projekte)`);
    } catch (e: any) {
      alert(e.message || 'Fehler bei der Synchronisierung');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#12131b] border border-white/[0.1] rounded-2xl w-full max-w-lg p-6 shadow-2xl flex flex-col gap-5">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <h2 className="text-base font-extrabold text-white flex items-center gap-2">
            <Cloud className="w-4 h-4 text-cyan-400" />
            <span>Google Drive & API Keys</span>
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-zinc-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-col gap-4">
          {/* Google Drive Path */}
          <div>
            <label className="text-xs font-bold text-zinc-300 block mb-1">
              Google Drive Beats Ordnerpfad:
            </label>
            <input
              type="text"
              value={config.gdrive_path}
              onChange={(e) => setConfig({ ...config, gdrive_path: e.target.value })}
              placeholder="G:\Meine Ablage\Beats"
              className="w-full bg-[#090a0f] border border-white/[0.1] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-cyan-500/50"
            />
            <span className="text-[11px] text-zinc-500 mt-1 block">
              Alle Beats, Artworks, 1440p Videos und Shorts werden hier automatisch versioniert gesichert.
            </span>
          </div>

          {/* Hugging Face Token */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-bold text-zinc-300">
                Hugging Face Token (FLUX.1 Live-Bildgenerierung):
              </label>
              <a
                href="https://huggingface.co/settings/tokens"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1"
              >
                <span>Token holen</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <input
              type="password"
              value={config.hf_api_key}
              onChange={(e) => setConfig({ ...config, hf_api_key: e.target.value })}
              placeholder="hf_..."
              className="w-full bg-[#090a0f] border border-white/[0.1] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-cyan-500/50"
            />
          </div>

          {/* Google Gemini API Key */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-bold text-zinc-300">
                Google Gemini API Key (KI-Metadaten & Titel):
              </label>
              <a
                href="https://aistudio.google.com/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1"
              >
                <span>Gratis Key holen</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <input
              type="password"
              value={config.gemini_api_key}
              onChange={(e) => setConfig({ ...config, gemini_api_key: e.target.value })}
              placeholder="AIzaSy..."
              className="w-full bg-[#090a0f] border border-white/[0.1] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-white/[0.08] pt-3 flex-wrap gap-2">
          <button
            onClick={handleSyncAll}
            disabled={syncing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs font-semibold text-zinc-200 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            <span>☁️ Alle mit Drive synchronisieren</span>
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-xs font-semibold text-white shadow-md shadow-purple-500/20"
          >
            <Save className="w-4 h-4" />
            <span>Speichern</span>
          </button>
        </div>
      </div>
    </div>
  );
};
