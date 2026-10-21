import React, { useState, useRef } from 'react';
import { X, Upload, Music, Loader2 } from 'lucide-react';
import { uploadMp3 } from '../api';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  showToast: (msg: string) => void;
  onUploadSuccess: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  showToast,
  onUploadSuccess,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.mp3') && !file.type.includes('audio')) {
      alert('Bitte wähle eine MP3-Audiodatei aus.');
      return;
    }
    setUploading(true);
    try {
      await uploadMp3(file, file.name);
      showToast(`Beat "${file.name}" hochgeladen & analysiert`);
      onUploadSuccess();
      onClose();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Hochladen');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#12131b] border border-white/[0.1] rounded-2xl w-full max-w-lg p-6 shadow-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <h2 className="text-base font-extrabold text-white flex items-center gap-2">
            <Music className="w-4 h-4 text-purple-400" />
            <span>Neuen Beat hochladen</span>
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-zinc-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Hidden Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp3,audio/*"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        {/* Drag Drop Area */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-200 ${
            isDragging
              ? 'border-purple-500 bg-purple-500/10'
              : 'border-white/[0.1] hover:border-purple-500/50 bg-[#090a0f]'
          }`}
        >
          {uploading ? (
            <div className="flex flex-col items-center gap-2 py-4">
              <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
              <div className="text-sm font-semibold text-white">Analysiere Audio & erstelle Artwork...</div>
              <div className="text-xs text-zinc-400">BPM, Key, Timestamps & Gemini Metadaten werden generiert</div>
            </div>
          ) : (
            <>
              <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400">
                <Upload className="w-6 h-6" />
              </div>
              <div className="text-center">
                <div className="text-sm font-bold text-white">+ MP3 hier ablegen oder klicken</div>
                <div className="text-xs text-zinc-500 mt-1">Unterstützt MP3-Exporte aus FL Studio, Ableton, Logic</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
