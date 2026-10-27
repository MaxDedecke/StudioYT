import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  Play,
  Pause,
  Cloud,
  Folder,
  Check,
  X,
  Sparkles,
  Upload,
  Video,
  FileText,
  Image as ImageIcon,
  ExternalLink,
  Download,
  Scissors,
  RefreshCw,
  Loader2,
  Copy,
  Save,
  Edit3,
  Music,
  Trash2,
} from 'lucide-react';
import type { Project, ThumbnailState } from '../types';
import {
  regenerateArtwork,
  uploadArtwork,
  analyzeArtwork,
  uploadVideoLoop,
  triggerRender,
  regenerateMetadata,
  saveMetadata,
  getThumbnails,
  generateThumbnails,
  selectThumbnail,
  uploadCustomThumbnail,
  deleteCustomThumbnail,
  openExplorerFolder,
  updateBeatAudio,
} from '../api';

interface BeatDetailPageProps {
  project: Project;
  onBack: () => void;
  onRefresh: () => void;
  onComplete: (name: string) => void;
  onDelete: (name: string) => void;
  showToast: (msg: string) => void;
}

const COMMON_KEYS = [
  "C Minor", "C# Minor", "D Minor", "D# Minor", "Eb Minor", "E Minor", "F Minor", "F# Minor", "G Minor", "G# Minor", "A Minor", "Bb Minor", "B Minor",
  "C Major", "C# Major", "D Major", "Eb Major", "E Major", "F Major", "F# Major", "G Major", "Ab Major", "A Major", "Bb Major", "B Major"
];

export const BeatDetailPage: React.FC<BeatDetailPageProps> = ({
  project,
  onBack,
  onRefresh,
  onComplete,
  onDelete,
  showToast,
}) => {
  const [activeTab, setActiveTab] = useState<'artwork' | 'video' | 'thumbnails' | 'release'>('artwork');

  // Audio Player State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(project.duration_sec || 0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Audio Info / BPM & Key editing state
  const [isEditingAudioInfo, setIsEditingAudioInfo] = useState(false);
  const [editBpm, setEditBpm] = useState<number>(project.bpm || 140);
  const [editKey, setEditKey] = useState<string>(project.key || 'C Minor');
  const [syncMetaWithBpm, setSyncMetaWithBpm] = useState<boolean>(true);
  const [isSavingAudioInfo, setIsSavingAudioInfo] = useState(false);

  useEffect(() => {
    setEditBpm(project.bpm || 140);
    setEditKey(project.key || 'C Minor');
    setMetadataText(project.metadata_text || '');
  }, [project.name, project.bpm, project.key, project.metadata_text]);

  const handleSaveAudioInfo = async () => {
    setIsSavingAudioInfo(true);
    try {
      const res = await updateBeatAudio(project.name, editBpm, editKey, syncMetaWithBpm);
      project.bpm = res.bpm;
      project.key = res.key;
      if (res.metadata_text) {
        project.metadata_text = res.metadata_text;
        setMetadataText(res.metadata_text);
      }
      showToast(`Tempo (${res.bpm} BPM) & Tonart (${res.key}) gespeichert!`);
      setIsEditingAudioInfo(false);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Speichern');
    } finally {
      setIsSavingAudioInfo(false);
    }
  };

  // Artwork & Video Upload
  const loopInputRef = useRef<HTMLInputElement | null>(null);
  const [isUploadingLoop, setIsUploadingLoop] = useState(false);
  const [isAnalyzingArtwork, setIsAnalyzingArtwork] = useState(false);

  // Video Studio State
  const [videoMode, setVideoMode] = useState<'main' | 'short'>('main');
  const [shortStart, setShortStart] = useState<number>(project.drop_sec || 12);
  const [shortDur, setShortDur] = useState<number>(30);
  const [isRendering, setIsRendering] = useState(false);

  // Thumbnail Studio State
  const [thumbState, setThumbState] = useState<ThumbnailState | null>(null);
  const [brandTagInput, setBrandTagInput] = useState('prodbyjmd');
  const [isGeneratingThumbs, setIsGeneratingThumbs] = useState(false);

  // Metadata / Release Suite State
  const [metadataText, setMetadataText] = useState(project.metadata_text || '');
  const [isEditingMeta, setIsEditingMeta] = useState(false);
  const [isRegeneratingMeta, setIsRegeneratingMeta] = useState(false);

  // Load thumbnail state on mount
  useEffect(() => {
    loadThumbs(true);
  }, [project.name]);

  const loadThumbs = async (initial = false) => {
    try {
      const data = await getThumbnails(project.name);
      setThumbState(data);
      if (initial && (data.brand_tag || data.default_artist)) {
        setBrandTagInput(data.brand_tag || data.default_artist || 'prodbyjmd');
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Audio Player Handlers
  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMeta = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || duration <= 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const target = ratio * duration;
    audioRef.current.currentTime = target;
    setCurrentTime(target);
  };

  const formatSec = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = Math.floor(s % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  // Helpers to extract visual analysis vs pure video prompt
  const extractCleanPrompt = (raw: string) => {
    const match = raw.match(/```(?:text)?\s*([\s\S]*?)```/);
    if (match && match[1]) {
      return match[1].trim();
    }
    return raw.trim();
  };

  const extractAnalysis = (raw: string) => {
    const match = raw.match(/### 🔍 Bild-Analyse:\s*([\s\S]*?)(?=### 🎬|$)/);
    if (match && match[1]) {
      return match[1].trim();
    }
    return null;
  };

  // Actions
  const artUploadRef = useRef<HTMLInputElement | null>(null);
  const [isUploadingArt, setIsUploadingArt] = useState(false);

  const handleUploadArtwork = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploadingArt(true);
    showToast('Lade eigenes Beat-Bild hoch & starte KI-Vision-Analyse...');
    try {
      const res = await uploadArtwork(project.name, file);
      project.has_artwork = true;
      project.prompt_text = res.prompt_text;
      project.artwork_mtime = res.artwork_mtime;
      showToast('Eigenes Beat-Bild erfolgreich übernommen & Loop-Prompt aktualisiert!');
      loadThumbs(false);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Fehler beim Hochladen des Bildes');
    } finally {
      setIsUploadingArt(false);
      if (artUploadRef.current) artUploadRef.current.value = '';
    }
  };

  const handleRegenArtwork = async () => {
    showToast('Generiere neues Artwork & analysiere Bild für Gemini Loop...');
    try {
      await regenerateArtwork(project.name);
      showToast('Neues Artwork & maßgeschneiderter Loop-Prompt fertig!');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Bildwechsel');
    }
  };

  const handleAnalyzeArtwork = async () => {
    setIsAnalyzingArtwork(true);
    showToast('Gemini Vision analysiert das Cover für Loop-Mikrobewegungen...');
    try {
      const res = await analyzeArtwork(project.name);
      project.prompt_text = res.prompt_text;
      showToast('Bildanalyse abgeschlossen & Video-Prompt aktualisiert!');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler bei der Bildanalyse');
    } finally {
      setIsAnalyzingArtwork(false);
    }
  };

  const handleCopyPromptAndOpenGemini = async () => {
    if (project.prompt_text) {
      const cleanPrompt = extractCleanPrompt(project.prompt_text);
      try {
        await navigator.clipboard.writeText(cleanPrompt);
        showToast('Video-Prompt kopiert & Gemini geöffnet!');
      } catch (e) {
        console.error(e);
      }
    }
    window.open('https://gemini.google.com/app', '_blank');
  };

  const handleLoopSelected = async (file: File) => {
    setIsUploadingLoop(true);
    showToast('Lade Video-Loop hoch & starte Render-Pipeline...');
    try {
      await uploadVideoLoop(project.name, file);
      showToast('Rendering gestartet!');
      onRefresh();
      setActiveTab('video');
    } catch (e: any) {
      alert(e.message || 'Fehler beim Video-Upload');
    } finally {
      setIsUploadingLoop(false);
    }
  };

  const handleStartRender = async (mode: 'both' | 'main_only' | 'short_only') => {
    setIsRendering(true);
    const label =
      mode === 'main_only'
        ? '1440p YouTube-Video'
        : mode === 'short_only'
        ? '9:16 Short & Reel'
        : 'Beide Videos (1440p + Short)';
    showToast(`Rendere ${label}...`);
    try {
      await triggerRender(project.name, mode, shortStart, shortDur);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Rendern');
    } finally {
      setIsRendering(false);
    }
  };

  const handleGenerateThumbnails = async () => {
    setIsGeneratingThumbs(true);
    try {
      await generateThumbnails(project.name, brandTagInput.trim() || 'prodbyjmd');
      showToast('Brand-Thumbnails erfolgreich erstellt!');
      loadThumbs(false);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Erstellen der Thumbnails');
    } finally {
      setIsGeneratingThumbs(false);
    }
  };

  const handleSelectThumbnail = async (file: string) => {
    try {
      await selectThumbnail(project.name, file);
      showToast('Thumbnail ausgewählt (thumbnail.jpg)');
      loadThumbs(false);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Auswählen');
    }
  };

  const thumbInputRef = useRef<HTMLInputElement | null>(null);
  const [isUploadingThumb, setIsUploadingThumb] = useState(false);

  const handleCustomThumbUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploadingThumb(true);
    showToast('Lade eigenes Thumbnail hoch & optimiere auf 16:9...');
    try {
      const res = await uploadCustomThumbnail(project.name, file);
      setThumbState(res.state);
      project.has_thumbnail = true;
      showToast('Eigenes Thumbnail erfolgreich aktiviert!');
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Fehler beim Thumbnail-Upload');
    } finally {
      setIsUploadingThumb(false);
      if (thumbInputRef.current) thumbInputRef.current.value = '';
    }
  };

  const handleDeleteCustomThumbnail = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Eigenes Thumbnail entfernen und zu den generierten Styles zurückkehren?')) return;
    try {
      const res = await deleteCustomThumbnail(project.name);
      setThumbState(res.state);
      showToast('Eigenes Thumbnail entfernt');
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Fehler beim Entfernen');
    }
  };

  const handleRegenerateMetadata = async () => {
    setIsRegeneratingMeta(true);
    try {
      const res = await regenerateMetadata(project.name);
      setMetadataText(res.metadata_text);
      showToast('Neue KI-Titel & Release-Texte generiert');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Neugenerieren');
    } finally {
      setIsRegeneratingMeta(false);
    }
  };

  const handleSaveMetadata = async () => {
    try {
      await saveMetadata(project.name, metadataText);
      setIsEditingMeta(false);
      showToast('Metadaten gespeichert');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Speichern');
    }
  };

  const handleCopyText = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      showToast(`${label} kopiert!`);
    } catch (e) {
      console.error(e);
    }
  };

  const renderJob = project.render_job;
  const isJobActive = !!(renderJob && renderJob.active);
  const mainVideoUrl = `/projects/${project.name}/final_youtube_video.mp4?t=${project.main_video_mtime || project.updated_at || 0}`;
  const shortVideoUrl = `/projects/${project.name}/short_reel_video.mp4?t=${project.short_video_mtime || project.updated_at || 0}`;
  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  // Active render polling effect to keep UI 100% in sync while FFmpeg encodes
  useEffect(() => {
    if (!isJobActive && !isRendering) return;
    const timer = setInterval(() => {
      onRefresh();
    }, 1200);
    return () => clearInterval(timer);
  }, [isJobActive, isRendering]);

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto px-4 sm:px-6 py-6 pb-20">
      {/* Hidden file input for loop */}
      <input
        type="file"
        ref={loopInputRef}
        accept="video/mp4"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleLoopSelected(e.target.files[0]);
          }
        }}
      />

      {/* TOP BAR / BACK NAVIGATION */}
      <div className="flex items-center justify-between gap-4 flex-wrap border-b border-white/[0.08] pb-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-xs font-semibold text-zinc-300 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Zurück zur Übersicht</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => openExplorerFolder(project.name)}
            title="Projektordner in Explorer öffnen"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-medium text-zinc-300"
          >
            <Folder className="w-3.5 h-3.5 text-zinc-400" />
            <span>Ordner öffnen</span>
          </button>

          <button
            onClick={() => onComplete(project.name)}
            title="Beat abschließen"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-xs font-semibold text-emerald-400"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Abschließen</span>
          </button>

          <button
            onClick={() => onDelete(project.name)}
            title="Aus Dashboard entfernen"
            className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Hidden Artwork File Input */}
      <input
        ref={artUploadRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/jpg"
        className="hidden"
        onChange={handleUploadArtwork}
      />

      {/* HERO BEAT HEADER & AUDIO PLAYER */}
      <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 shadow-xl flex flex-col md:flex-row gap-6 items-start md:items-center">
        {/* Cover Preview (140x140) */}
        <div className="relative group w-36 h-36 rounded-xl overflow-hidden bg-black border border-white/[0.1] flex-shrink-0 shadow-lg">
          {project.has_artwork ? (
            <img
              src={`/projects/${project.name}/artwork.jpg?t=${project.artwork_mtime || project.updated_at || 0}`}
              alt={project.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-zinc-900 text-zinc-600">
              <ImageIcon className="w-8 h-8" />
            </div>
          )}
          <div className="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1.5 p-2 text-[11px] font-semibold text-white">
            <button
              onClick={() => artUploadRef.current?.click()}
              disabled={isUploadingArt}
              className="w-full py-1.5 px-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center gap-1.5 shadow text-xs font-bold transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Eigenes Bild</span>
            </button>
            <button
              onClick={handleRegenArtwork}
              className="w-full py-1 px-2 rounded-lg bg-white/[0.1] hover:bg-white/[0.2] text-zinc-200 flex items-center justify-center gap-1 text-[11px] transition-colors"
            >
              <Sparkles className="w-3 h-3 text-purple-400" />
              <span>KI-Bild</span>
            </button>
          </div>
        </div>

        {/* Info & Player */}
        <div className="flex-1 flex flex-col gap-3.5 w-full min-w-0">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-black tracking-wide text-white uppercase">
                {project.name}
              </h1>

              {/* Editable BPM & Key Badge */}
              <button
                onClick={() => setIsEditingAudioInfo(!isEditingAudioInfo)}
                title="BPM & Tonart (Key) bearbeiten"
                className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/15 hover:bg-purple-500/25 border border-purple-500/30 text-purple-300 hover:text-white text-xs font-bold transition-all shadow-sm group/btn"
              >
                <span>{project.bpm || 140} BPM · {project.key || 'C Minor'}</span>
                <Edit3 className="w-3.5 h-3.5 text-purple-400 group-hover/btn:text-white transition-colors" />
              </button>

              {project.is_backed_up ? (
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center gap-1">
                  <Cloud className="w-3.5 h-3.5" />
                  <span>Google Drive gesichert</span>
                </span>
              ) : null}
              {isJobActive && (
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1 animate-pulse">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Rendert {renderJob?.percent || 0}%</span>
                </span>
              )}
            </div>

            {/* Inline BPM & Key Editor Popover */}
            {isEditingAudioInfo && (
              <div className="mt-3.5 bg-[#090a12] border border-purple-500/40 rounded-xl p-4 shadow-2xl flex flex-col gap-3.5 animate-in fade-in duration-200">
                <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-white">
                    <Music className="w-4 h-4 text-purple-400" />
                    <span>Tempo (BPM) & Tonart (Key) manuell korrigieren</span>
                  </div>
                  <button
                    onClick={() => setIsEditingAudioInfo(false)}
                    className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-white/[0.06]"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {/* BPM Field */}
                  <div>
                    <label className="text-[11px] font-bold text-zinc-400 block mb-1">
                      Tempo (BPM)
                    </label>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => setEditBpm(Math.max(40, editBpm - 1))}
                        className="w-8 h-9 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-zinc-300 font-bold text-sm flex items-center justify-center"
                      >
                        -
                      </button>
                      <input
                        type="number"
                        min="40"
                        max="240"
                        value={editBpm}
                        onChange={(e) => setEditBpm(parseInt(e.target.value) || 140)}
                        className="flex-1 bg-[#12131e] border border-white/[0.12] focus:border-purple-500/60 rounded-lg px-3 py-1.5 text-xs font-bold text-white text-center outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setEditBpm(Math.min(240, editBpm + 1))}
                        className="w-8 h-9 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-zinc-300 font-bold text-sm flex items-center justify-center"
                      >
                        +
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditBpm(Math.round(editBpm / 2))}
                        title="Halbieren (z. B. 160 -> 80)"
                        className="px-2 h-9 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-[10px] text-zinc-400 hover:text-white"
                      >
                        ÷2
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditBpm(Math.round(editBpm * 2))}
                        title="Verdoppeln (z. B. 75 -> 150)"
                        className="px-2 h-9 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-[10px] text-zinc-400 hover:text-white"
                      >
                        ×2
                      </button>
                    </div>
                  </div>

                  {/* Key Field */}
                  <div>
                    <label className="text-[11px] font-bold text-zinc-400 block mb-1">
                      Tonart (Key)
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        list="key-suggestions"
                        value={editKey}
                        onChange={(e) => setEditKey(e.target.value)}
                        placeholder="z. B. D# Minor, C Minor..."
                        className="flex-1 bg-[#12131e] border border-white/[0.12] focus:border-purple-500/60 rounded-lg px-3 py-1.5 text-xs font-bold text-white outline-none"
                      />
                      <datalist id="key-suggestions">
                        {COMMON_KEYS.map((k) => (
                          <option key={k} value={k} />
                        ))}
                      </datalist>
                    </div>
                  </div>
                </div>

                {/* Quick Key Chips */}
                <div>
                  <div className="text-[10px] font-semibold text-zinc-500 mb-1">Schnell-Auswahl Tonarten:</div>
                  <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto">
                    {COMMON_KEYS.map((k) => (
                      <button
                        key={k}
                        type="button"
                        onClick={() => setEditKey(k)}
                        className={`text-[10px] px-2 py-0.5 rounded-md border transition-all ${
                          editKey.toLowerCase() === k.toLowerCase()
                            ? 'bg-purple-500/30 border-purple-500/70 text-purple-200 font-bold'
                            : 'bg-white/[0.03] border-white/[0.06] text-zinc-400 hover:text-zinc-200'
                        }`}
                      >
                        {k}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sync Metadata Checkbox */}
                <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer pt-1 select-none">
                  <input
                    type="checkbox"
                    checked={syncMetaWithBpm}
                    onChange={(e) => setSyncMetaWithBpm(e.target.checked)}
                    className="rounded border-zinc-700 text-purple-600 focus:ring-purple-500 bg-zinc-900 w-4 h-4"
                  />
                  <span>YouTube Titel, Beschreibung & Timestamps automatisch mit neuen Audio-Daten aktualisieren</span>
                </label>

                {/* Action Buttons */}
                <div className="flex items-center justify-end gap-2 pt-1 border-t border-white/[0.06]">
                  <button
                    type="button"
                    onClick={() => setIsEditingAudioInfo(false)}
                    className="px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs font-semibold text-zinc-300"
                  >
                    Abbrechen
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveAudioInfo}
                    disabled={isSavingAudioInfo}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-md shadow-purple-500/20 disabled:opacity-50"
                  >
                    {isSavingAudioInfo ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Aktualisiere...</span>
                      </>
                    ) : (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Speichern & Daten übernehmen</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {project.vibe && (
              <p className="text-xs text-zinc-400 mt-1 font-medium">{project.vibe}</p>
            )}
          </div>

          {/* Interactive Scrub Bar Audio Player */}
          {project.has_mp3 && (
            <div className="flex items-center gap-3.5 bg-[#090a0f] border border-white/[0.06] p-3 rounded-xl w-full">
              <button
                onClick={togglePlay}
                className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white flex items-center justify-center shadow-lg shadow-purple-500/20 flex-shrink-0"
              >
                {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
              </button>

              <div onClick={handleSeek} className="flex-1 h-4 flex items-center cursor-pointer group">
                <div className="w-full bg-white/[0.08] h-2 rounded-full overflow-hidden group-hover:h-2.5 transition-all">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-cyan-400 h-full rounded-full"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              <div className="text-xs text-zinc-400 font-mono flex-shrink-0">
                {formatSec(currentTime)} / {project.duration_str || '--:--'}
              </div>

              <audio
                ref={audioRef}
                src={`/projects/${project.name}/beat.mp3`}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMeta}
                onEnded={() => setIsPlaying(false)}
              />
            </div>
          )}
        </div>
      </div>

      {/* LIVE RENDER MONITOR (Visible whenever FFmpeg renders in background) */}
      {isJobActive && (
        <div className="bg-[#11121c] border border-amber-500/30 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-bold text-amber-400 flex items-center gap-2 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{renderJob?.stage_label || 'Rendere Video-Pipeline...'}</span>
            </span>
            <span className="font-extrabold text-white text-base">{renderJob?.percent || 0}%</span>
          </div>
          <div className="w-full bg-white/[0.08] rounded-full h-2.5 overflow-hidden mb-2.5">
            <div
              className="bg-gradient-to-r from-amber-500 via-purple-500 to-cyan-400 h-full rounded-full transition-all duration-300"
              style={{ width: `${renderJob?.percent || 0}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <div className="flex gap-4">
              {renderJob?.mode !== 'short_only' && (
                <span>1440p YouTube: <strong className="text-zinc-200">{renderJob?.main_percent || 0}%</strong></span>
              )}
              {renderJob?.mode !== 'main_only' && (
                <span>Short / Reel: <strong className="text-zinc-200">{renderJob?.short_percent || 0}%</strong></span>
              )}
            </div>
            <div>
              {renderJob?.current_time_str} · {renderJob?.speed} · ETA: {renderJob?.eta_str}
            </div>
          </div>
        </div>
      )}

      {/* WORKSPACE NAVIGATION TABS */}
      <div className="flex items-center gap-2 border-b border-white/[0.08] overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab('artwork')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'artwork'
              ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-md'
              : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>1. Artwork & Loop</span>
        </button>

        <button
          onClick={() => setActiveTab('video')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'video'
              ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-md'
              : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Video className="w-4 h-4 text-emerald-400" />
          <span>2. Video Studio (1440p & Reel)</span>
          {(project.has_final_video || project.has_short_video) && (
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
          )}
        </button>

        <button
          onClick={() => setActiveTab('thumbnails')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'thumbnails'
              ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-md'
              : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <ImageIcon className="w-4 h-4 text-cyan-400" />
          <span>3. YouTube Thumbnail Studio</span>
          {project.has_thumbnail ? <span className="w-2 h-2 rounded-full bg-cyan-400" /> : null}
        </button>

        <button
          onClick={() => setActiveTab('release')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'release'
              ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-md'
              : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <FileText className="w-4 h-4 text-amber-400" />
          <span>4. Release Suite & SEO</span>
        </button>
      </div>

      {/* TAB CONTENT AREAS */}

      {/* TAB 1: ARTWORK & LOOP */}
      {activeTab === 'artwork' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cover & Bildwechsel */}
          <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>Lithen Green-Night Artwork</span>
              </h2>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => artUploadRef.current?.click()}
                  disabled={isUploadingArt}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.08] hover:bg-white/[0.14] border border-white/[0.1] text-white text-xs font-semibold shadow transition-colors"
                >
                  {isUploadingArt ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Lade hoch...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Eigenes Bild hochladen</span>
                    </>
                  )}
                </button>
                <button
                  onClick={handleAnalyzeArtwork}
                  disabled={isAnalyzingArtwork}
                  title="Bild erneut mit Gemini Vision auf Mikrobewegungen analysieren"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-zinc-200 text-xs font-semibold disabled:opacity-50 transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzingArtwork ? 'animate-spin' : ''}`} />
                  <span>Bild analysieren</span>
                </button>
                <button
                  onClick={handleRegenArtwork}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Neues KI-Bild</span>
                </button>
              </div>
            </div>

            <div className="aspect-video rounded-xl overflow-hidden bg-black border border-white/[0.08] relative group">
              <img
                src={`/projects/${project.name}/artwork.jpg?t=${project.artwork_mtime || project.updated_at || 0}`}
                alt="Artwork"
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-3 left-3 bg-black/75 backdrop-blur-md px-3 py-1 rounded-md text-[11px] text-zinc-300 border border-white/10">
                1:1 Widescreen Grade · 2560x1440 Master
              </div>
            </div>

            <div className="p-3 bg-[#090a0f] border border-white/[0.06] rounded-xl flex items-center gap-2.5 text-xs text-zinc-400">
              <Cloud className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span>
                <strong>Google Drive Auto-Sync:</strong> Du kannst dein Bild direkt hier hochladen oder einfach die Datei <code className="text-white font-mono bg-white/[0.08] px-1 py-0.5 rounded">artwork.jpg</code> in deinem Google Drive Beat-Ordner austauschen. Das System übernimmt es automatisch.
              </span>
            </div>

            <p className="text-xs text-zinc-400 leading-relaxed">
              Jedes Artwork durchläuft die Lithen Night-Cam Pipeline (Direct iPhone 15 Pro Flash, analoges Film-Korn, 1:1 Cover auf 16:9-Schwarzbalken). Nie wieder Copyright-Stress durch einzigartige Synthese.
            </p>
          </div>

          {/* Gemini Video-Loop Generator */}
          <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Video className="w-4 h-4 text-cyan-400" />
                <span>Gemini Video Loop Generator</span>
              </h2>
              {isAnalyzingArtwork && (
                <span className="text-xs text-cyan-400 font-semibold flex items-center gap-1 animate-pulse">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Analysiere Bild...</span>
                </span>
              )}
            </div>

            {/* Display Visual Analysis Box if available */}
            {extractAnalysis(project.prompt_text || '') && (
              <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-3.5">
                <div className="text-xs font-bold text-cyan-300 flex items-center gap-1.5 mb-1">
                  <span>🔍 Visuelle Bild-Analyse:</span>
                </div>
                <div className="text-xs text-zinc-300 leading-relaxed">
                  {extractAnalysis(project.prompt_text || '')}
                </div>
              </div>
            )}

            {/* Clean Prompt Box */}
            <div>
              <div className="text-[11px] font-bold text-zinc-400 mb-1 flex items-center justify-between">
                <span>Maßgeschneiderter Prompt (Nur Mikrobewegungen):</span>
                <span className="text-[10px] text-zinc-500">100% starr, kein Morphen</span>
              </div>
              <div className="bg-[#090a0f] border border-white/[0.08] rounded-xl p-3.5 relative">
                <div className="text-[11px] font-mono text-zinc-200 max-h-28 overflow-y-auto leading-relaxed whitespace-pre-wrap select-text">
                  {extractCleanPrompt(project.prompt_text || '') || 'Kein Prompt hinterlegt. Klicke auf "Bild analysieren".'}
                </div>
              </div>
            </div>

            <button
              onClick={handleCopyPromptAndOpenGemini}
              className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition-colors"
            >
              <Copy className="w-4 h-4" />
              <span>Prompt kopieren & Gemini öffnen</span>
              <ExternalLink className="w-3.5 h-3.5 opacity-70" />
            </button>

            {/* Video Loop Drop Zone */}
            <div
              onClick={() => loopInputRef.current?.click()}
              className="border-2 border-dashed border-white/[0.12] hover:border-cyan-500/50 rounded-2xl p-5 flex flex-col items-center justify-center gap-2 cursor-pointer bg-[#090a0f] transition-all"
            >
              {isUploadingLoop ? (
                <div className="flex flex-col items-center gap-2 py-2">
                  <Loader2 className="w-7 h-7 text-cyan-400 animate-spin" />
                  <span className="text-xs font-semibold text-white">Lade Video-Loop hoch...</span>
                </div>
              ) : (
                <>
                  <div className="w-9 h-9 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                    <Upload className="w-4 h-4" />
                  </div>
                  <div className="text-center">
                    <div className="text-xs font-bold text-white">Animierte MP4 hier ablegen oder klicken</div>
                    <div className="text-[11px] text-zinc-500 mt-0.5">
                      {project.has_video_loop ? '✓ Loop bereits vorhanden (Klicken zum Ersetzen)' : 'Startet automatisch das 1440p- und Short-Rendering'}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: VIDEO STUDIO */}
      {activeTab === 'video' && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Large Video Player */}
            <div className="lg:col-span-2 bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex bg-[#090a0f] border border-white/[0.08] p-1 rounded-xl">
                  <button
                    onClick={() => setVideoMode('main')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                      videoMode === 'main' ? 'bg-purple-600 text-white shadow' : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    1440p YouTube (16:9)
                  </button>
                  <button
                    onClick={() => setVideoMode('short')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                      videoMode === 'short' ? 'bg-purple-600 text-white shadow' : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    Short / Instagram Reel (9:16)
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleStartRender(videoMode === 'main' ? 'main_only' : 'short_only')}
                    disabled={isRendering || isJobActive}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/35 border border-purple-500/40 text-purple-200 hover:text-white text-xs font-semibold disabled:opacity-50 transition-colors shadow-sm"
                    title={videoMode === 'main' ? 'Nur das 1440p YouTube-Video neu rendern' : 'Nur das 9:16 Short neu rendern'}
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isRendering || isJobActive ? 'animate-spin' : ''}`} />
                    <span>{videoMode === 'main' ? '1440p einzeln rendern' : 'Short einzeln rendern'}</span>
                  </button>

                  <a
                    href={videoMode === 'main' ? mainVideoUrl : shortVideoUrl}
                    download={videoMode === 'main' ? `${project.name}_1440p.mp4` : `${project.name}_reel.mp4`}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs font-semibold text-zinc-200"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>MP4 herunterladen</span>
                  </a>
                </div>
              </div>

              {/* Player */}
              <div className="bg-black rounded-xl overflow-hidden border border-white/[0.08] flex items-center justify-center min-h-[380px] p-2">
                {videoMode === 'main' ? (
                  project.has_final_video ? (
                    <video key={mainVideoUrl} src={mainVideoUrl} controls playsInline className="w-full aspect-video rounded-lg" />
                  ) : (
                    <div className="text-center py-16 text-zinc-500 text-xs">
                      Noch kein 1440p Hauptvideo gerendert.
                    </div>
                  )
                ) : project.has_short_video ? (
                  <video key={shortVideoUrl} src={shortVideoUrl} controls playsInline className="h-[460px] aspect-[9/16] rounded-lg" />
                ) : (
                  <div className="text-center py-16 text-zinc-500 text-xs">
                    Noch kein 9:16 Short/Reel gerendert.
                  </div>
                )}
              </div>

              {/* Video Source Indicator */}
              <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#090a0f] border border-white/[0.06] text-xs text-zinc-400">
                {project.has_video_loop ? (
                  <span className="flex items-center gap-1.5 text-cyan-400 font-semibold">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Basis: Dynamischer Gemini Video-Loop (video_loop.mp4)</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-zinc-300 font-medium">
                    <ImageIcon className="w-3.5 h-3.5 text-purple-400" />
                    <span>Basis: <strong>Brand-Thumbnail</strong> ({project.has_thumbnail ? 'thumbnail.jpg' : 'artwork.jpg'}) + Beat — Reines Standbild, keine Fremd-Effekte</span>
                  </span>
                )}
              </div>
            </div>

            {/* Right Col: Recut & Render Settings */}
            <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col justify-between gap-5">
              <div className="flex flex-col gap-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Scissors className="w-4 h-4 text-purple-400" />
                  <span>Short & Reel Schnitt</span>
                </h3>

                <div>
                  <label className="text-xs text-zinc-400 font-medium block mb-1.5">
                    Startpunkt im Beat:
                  </label>
                  <select
                    value={shortStart}
                    onChange={(e) => setShortStart(Number(e.target.value))}
                    className="w-full bg-[#090a0f] border border-white/[0.1] rounded-xl px-3.5 py-2 text-xs text-white outline-none cursor-pointer"
                  >
                    <option value={0}>Ab 0:00 (Intro)</option>
                    <option value={12}>Ab 0:12 (Drop / Hook)</option>
                    <option value={15}>Ab 0:15 (Hook)</option>
                    <option value={30}>Ab 0:30 (Part / Verse)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-zinc-400 font-medium block mb-1.5">
                    Dauer des Clips:
                  </label>
                  <select
                    value={shortDur}
                    onChange={(e) => setShortDur(Number(e.target.value))}
                    className="w-full bg-[#090a0f] border border-white/[0.1] rounded-xl px-3.5 py-2 text-xs text-white outline-none cursor-pointer"
                  >
                    <option value={30}>30 Sekunden (Optimal für Reels)</option>
                    <option value={45}>45 Sekunden</option>
                    <option value={58}>58 Sekunden (Max Short)</option>
                  </select>
                </div>

                <div className="p-3 bg-[#090a0f] border border-white/[0.05] rounded-xl text-[11px] text-zinc-400 leading-relaxed flex items-center justify-between gap-2">
                  <div>
                    💡 Eingebrannte Typo bei Sek. 5: <span className="text-white font-bold">{project.key} · {project.bpm} BPM</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingAudioInfo(true);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    className="text-[11px] text-purple-400 hover:text-purple-300 font-semibold underline flex-shrink-0"
                  >
                    BPM / Key anpassen
                  </button>
                </div>
              </div>

              {/* Render Action Buttons */}
              <div className="flex flex-col gap-2.5 pt-4 border-t border-white/[0.08]">
                <div className="text-[11px] font-bold text-zinc-400 mb-0.5 flex items-center justify-between">
                  <span>Render-Optionen:</span>
                  <span className="text-zinc-500 font-normal">Separat oder beides</span>
                </div>

                {/* Nur 1440p YouTube-Video */}
                <button
                  onClick={() => handleStartRender('main_only')}
                  disabled={isRendering || isJobActive}
                  className="w-full py-2.5 px-3.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/35 border border-purple-500/40 disabled:opacity-50 text-purple-200 hover:text-white text-xs font-semibold shadow-sm flex items-center justify-between gap-2 transition-all group"
                >
                  <div className="flex items-center gap-2">
                    <Video className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
                    <span>Nur 1440p YouTube-Video rendern</span>
                  </div>
                  <span className="text-[10px] bg-purple-500/30 px-2 py-0.5 rounded text-purple-300 font-mono font-bold">16:9</span>
                </button>

                {/* Nur 9:16 Short & Reel */}
                <button
                  onClick={() => handleStartRender('short_only')}
                  disabled={isRendering || isJobActive}
                  className="w-full py-2.5 px-3.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/35 border border-indigo-500/40 disabled:opacity-50 text-indigo-200 hover:text-white text-xs font-semibold shadow-sm flex items-center justify-between gap-2 transition-all group"
                >
                  <div className="flex items-center gap-2">
                    <Scissors className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
                    <span>Nur 9:16 Short & Reel neu schneiden</span>
                  </div>
                  <span className="text-[10px] bg-indigo-500/30 px-2 py-0.5 rounded text-indigo-300 font-mono font-bold">9:16</span>
                </button>

                {/* Beide gleichzeitig */}
                <button
                  onClick={() => handleStartRender('both')}
                  disabled={isRendering || isJobActive}
                  className="w-full py-2.5 px-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-purple-500/20 flex items-center justify-center gap-2 transition-all"
                >
                  <RefreshCw className={`w-4 h-4 ${isRendering || isJobActive ? 'animate-spin' : ''}`} />
                  <span>Beide neu rendern (1440p + Short)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: THUMBNAIL STUDIO */}
      {activeTab === 'thumbnails' && (
        <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-6">
          <input
            ref={thumbInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/jpg"
            className="hidden"
            onChange={handleCustomThumbUpload}
          />

          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>prodbyJMD Brand Thumbnail Studio</span>
              </h2>
              <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
                Wähle aus deinen 5 generierten Brand-Aesthetics mit <strong className="text-purple-300">prodbyjmd</strong> oder lade dein eigenes Custom-Thumbnail hoch (wird automatisch auf 16:9 YouTube 1280×720 skaliert).
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 mt-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-[11px] font-semibold text-purple-300">
                <Video className="w-3.5 h-3.5 text-purple-400" />
                <span>Dieses Brand-Thumbnail wird automatisch als Bildquelle für das 1440p YouTube-Video &amp; Short verwendet.</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 flex-wrap">
              <button
                type="button"
                onClick={() => thumbInputRef.current?.click()}
                disabled={isUploadingThumb}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-md shadow-purple-500/20 disabled:opacity-50 transition-colors"
              >
                {isUploadingThumb ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Optimiere & aktiviere...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Eigenes Thumbnail hochladen</span>
                  </>
                )}
              </button>

              {thumbState?.has_selected && (
                <a
                  href={`/projects/${project.name}/thumbnail.jpg?t=${project.updated_at || 0}`}
                  download={`${project.name}_thumbnail.jpg`}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-500/20"
                >
                  <Download className="w-4 h-4" />
                  <span>Aktives Thumbnail herunterladen</span>
                </a>
              )}
            </div>
          </div>

          {/* Brand Tag Input Row */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 bg-[#090a0f] border border-white/[0.08] p-3.5 rounded-2xl">
            <div className="flex items-center gap-2 flex-1">
              <span className="text-xs font-bold text-zinc-400 whitespace-nowrap">Brand / Watermark:</span>
              <input
                type="text"
                value={brandTagInput}
                onChange={(e) => setBrandTagInput(e.target.value)}
                placeholder="prodbyjmd"
                className="flex-1 bg-[#12131e] border border-white/[0.1] focus:border-purple-500/60 rounded-xl px-3.5 py-2 text-xs font-bold text-white placeholder-zinc-500 outline-none"
              />
            </div>

            {/* Quick Tag Presets */}
            <div className="flex items-center gap-1.5 flex-wrap">
              {['prodbyjmd', '@prodbyJMD', 'PRODBYJMD'].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setBrandTagInput(t)}
                  className={`text-[11px] px-2.5 py-1 rounded-lg border transition-all ${
                    brandTagInput === t
                      ? 'bg-purple-500/20 border-purple-500/60 text-purple-200 font-bold'
                      : 'bg-white/[0.04] border-white/[0.06] text-zinc-400 hover:text-white'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <button
              onClick={handleGenerateThumbnails}
              disabled={isGeneratingThumbs}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-purple-500/20 flex items-center justify-center gap-2 flex-shrink-0"
            >
              {isGeneratingThumbs ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Erstelle Styles...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Styles neu generieren</span>
                </>
              )}
            </button>
          </div>

          {/* Grid of Brand Thumbnails + Upload Option */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {/* Upload Card for Custom Thumbnail (if not yet uploaded) */}
            {!thumbState?.variants.some((v) => v.includes('custom_uploaded')) && (
              <div
                onClick={() => thumbInputRef.current?.click()}
                className="p-4 rounded-2xl border-2 border-dashed border-purple-500/40 hover:border-purple-400/80 cursor-pointer bg-purple-500/[0.04] hover:bg-purple-500/[0.08] transition-all flex flex-col items-center justify-center gap-2.5 min-h-[170px] group"
              >
                <div className="w-10 h-10 rounded-full bg-purple-500/20 group-hover:bg-purple-500/30 text-purple-300 flex items-center justify-center transition-colors">
                  {isUploadingThumb ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
                </div>
                <div className="text-center">
                  <div className="text-xs font-bold text-white group-hover:text-purple-200 transition-colors">
                    Eigenes Thumbnail hochladen
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-1">
                    PNG, JPG oder WEBP (16:9 auto)
                  </div>
                </div>
              </div>
            )}

            {thumbState?.variants.map((v) => {
              const isSelected = thumbState.selected_src === v;
              const fname = v.split('/').pop() || '';
              const isCustom = fname === 'custom_uploaded.jpg';
              const styleName = thumbState.style_labels?.[fname] || fname.replace('.jpg', '').replace('style_', 'Style ');

              return (
                <div
                  key={v}
                  onClick={() => handleSelectThumbnail(v)}
                  className={`p-2.5 rounded-2xl cursor-pointer transition-all duration-200 border-2 relative group/card ${
                    isSelected
                      ? 'bg-emerald-500/10 border-emerald-500 shadow-xl shadow-emerald-500/15'
                      : isCustom
                      ? 'bg-[#120e1d] border-purple-500/30 hover:border-purple-500/60'
                      : 'bg-[#0d0e15] border-white/[0.06] hover:border-purple-500/40'
                  }`}
                >
                  <div className="relative aspect-video rounded-xl overflow-hidden bg-black">
                    <img
                      src={`/projects/${project.name}/${v}?t=${project.updated_at || 0}`}
                      alt={styleName}
                      className="w-full h-full object-cover"
                    />
                    {isSelected && (
                      <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-emerald-500 text-black text-[10px] font-extrabold flex items-center gap-1 shadow-md">
                        <Check className="w-3 h-3 stroke-[3]" />
                        <span>AKTIV</span>
                      </div>
                    )}
                    {isCustom && !isSelected && (
                      <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-purple-600/90 text-white text-[10px] font-bold shadow-md">
                        CUSTOM
                      </div>
                    )}
                    {isCustom && (
                      <button
                        type="button"
                        onClick={handleDeleteCustomThumbnail}
                        title="Eigenes Thumbnail löschen"
                        className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/70 hover:bg-red-600 text-zinc-300 hover:text-white transition-colors shadow"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                    {project.duration_str && project.duration_str !== '--:--' && (
                      <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/85 text-white text-[10px] font-semibold">
                        {project.duration_str}
                      </div>
                    )}
                  </div>

                  <div className="mt-2.5 px-1">
                    <div className="flex items-center justify-between gap-1">
                      <div className="text-xs font-bold text-zinc-200 truncate">
                        {styleName}
                      </div>
                      {isCustom && (
                        <span className="text-[10px] font-bold text-purple-400 bg-purple-500/20 px-1.5 py-0.5 rounded flex-shrink-0">
                          Dein Upload
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-zinc-500 mt-0.5">
                      {isSelected ? '✓ Aktives YouTube-Thumbnail' : 'Klicken zum Aktivieren'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: RELEASE & SEO SUITE */}
      {activeTab === 'release' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Markdown Content Box */}
          <div className="lg:col-span-2 bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-amber-400" />
                <span>YouTube & Instagram Metadaten</span>
              </h2>
              <div className="flex items-center gap-2">
                {isEditingMeta ? (
                  <button
                    onClick={handleSaveMetadata}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>Speichern</span>
                  </button>
                ) : (
                  <button
                    onClick={() => setIsEditingMeta(true)}
                    className="px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-xs font-semibold text-zinc-200"
                  >
                    Bearbeiten
                  </button>
                )}
                <button
                  onClick={handleRegenerateMetadata}
                  disabled={isRegeneratingMeta}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-xs font-semibold text-zinc-200 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRegeneratingMeta ? 'animate-spin' : ''}`} />
                  <span>↻ Neu generieren</span>
                </button>
              </div>
            </div>

            {/* Audio Basis Banner */}
            <div className="flex items-center justify-between gap-3 bg-[#090a0f] border border-white/[0.06] rounded-xl px-4 py-2.5">
              <div className="flex items-center gap-2 text-xs text-zinc-300">
                <Music className="w-3.5 h-3.5 text-purple-400" />
                <span>Audio-Basis für Titel & Beschreibung:</span>
                <span className="font-bold text-white px-2 py-0.5 rounded bg-purple-500/20 border border-purple-500/30">
                  {project.bpm || 140} BPM · {project.key || 'C Minor'}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsEditingAudioInfo(true);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                className="text-xs text-purple-400 hover:text-purple-300 font-semibold underline"
              >
                Tempo / Key ändern
              </button>
            </div>

            {isEditingMeta ? (
              <textarea
                value={metadataText}
                onChange={(e) => setMetadataText(e.target.value)}
                rows={18}
                className="w-full bg-[#090a0f] border border-white/[0.12] rounded-xl p-4 text-xs font-mono text-zinc-200 outline-none focus:border-purple-500/50 leading-relaxed"
              />
            ) : (
              <pre className="w-full bg-[#090a0f] border border-white/[0.08] rounded-xl p-4 text-xs font-mono text-zinc-300 overflow-x-auto max-h-[60vh] whitespace-pre-wrap leading-relaxed select-text">
                {metadataText || 'Keine Metadaten vorhanden. Klicke auf "Neu generieren".'}
              </pre>
            )}
          </div>

          {/* Right Col: Quick 1-Click Copy Panels & External Links */}
          <div className="flex flex-col gap-5">
            {/* 1-Click Copy Actions */}
            <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-3">
              <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-1">
                1-Klick Aktionen
              </h3>

              <button
                onClick={() => handleCopyText(metadataText, 'Komplettes Release-Paket')}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-md shadow-purple-500/20"
              >
                <Copy className="w-4 h-4" />
                <span>Alles kopieren</span>
              </button>

              <button
                onClick={() => {
                  const match = metadataText.match(/## 📱 Instagram Reel[\s\S]*?```(?:text)?\s*([\s\S]*?)```/);
                  handleCopyText(match && match[1] ? match[1].trim() : metadataText, 'IG Reel Caption');
                }}
                className="w-full py-2 px-4 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-zinc-200 text-xs font-semibold flex items-center justify-center gap-2"
              >
                <span>IG Reel Caption kopieren</span>
              </button>

              <button
                onClick={() => {
                  const match = metadataText.match(/## 🏷️ YouTube Studio Tags[\s\S]*?\n([\s\S]*?)$/);
                  handleCopyText(match && match[1] ? match[1].trim() : '', 'YouTube SEO Tags');
                }}
                className="w-full py-2 px-4 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-zinc-200 text-xs font-semibold flex items-center justify-center gap-2"
              >
                <span>YouTube SEO Tags kopieren</span>
              </button>
            </div>

            {/* Direct Channel Links */}
            <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-3">
              <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-1">
                Upload & Release
              </h3>

              <a
                href="https://studio.youtube.com/channel/upload"
                target="_blank"
                rel="noreferrer"
                className="w-full py-2 px-4 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-zinc-200 text-xs font-semibold flex items-center justify-between"
              >
                <span>YouTube Studio Upload</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-60" />
              </a>

              <a
                href="https://www.instagram.com/"
                target="_blank"
                rel="noreferrer"
                className="w-full py-2 px-4 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-zinc-200 text-xs font-semibold flex items-center justify-between"
              >
                <span>Instagram Web</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-60" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
