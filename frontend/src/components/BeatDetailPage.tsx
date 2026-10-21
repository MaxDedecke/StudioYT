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
} from 'lucide-react';
import type { Project, ThumbnailState } from '../types';
import {
  regenerateArtwork,
  uploadVideoLoop,
  triggerRender,
  regenerateMetadata,
  saveMetadata,
  getThumbnails,
  generateThumbnails,
  selectThumbnail,
  openExplorerFolder,
} from '../api';

interface BeatDetailPageProps {
  project: Project;
  onBack: () => void;
  onRefresh: () => void;
  onComplete: (name: string) => void;
  onDelete: (name: string) => void;
  showToast: (msg: string) => void;
}

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

  // Artwork & Video Upload
  const loopInputRef = useRef<HTMLInputElement | null>(null);
  const [isUploadingLoop, setIsUploadingLoop] = useState(false);

  // Video Studio State
  const [videoMode, setVideoMode] = useState<'main' | 'short'>('main');
  const [shortStart, setShortStart] = useState<number>(project.drop_sec || 12);
  const [shortDur, setShortDur] = useState<number>(30);
  const [isRendering, setIsRendering] = useState(false);

  // Thumbnail Studio State
  const [thumbState, setThumbState] = useState<ThumbnailState | null>(null);
  const [artistInput, setArtistInput] = useState('');
  const [isGeneratingThumbs, setIsGeneratingThumbs] = useState(false);
  const [pollingThumbs, setPollingThumbs] = useState(false);

  // Metadata / Release Suite State
  const [metadataText, setMetadataText] = useState(project.metadata_text || '');
  const [isEditingMeta, setIsEditingMeta] = useState(false);
  const [isRegeneratingMeta, setIsRegeneratingMeta] = useState(false);

  // Load thumbnail state on mount / tab change
  useEffect(() => {
    loadThumbs(true);
  }, [project.name]);

  const loadThumbs = async (initial = false) => {
    try {
      const data = await getThumbnails(project.name);
      setThumbState(data);
      if (initial && data.default_artist) {
        setArtistInput(data.default_artist);
      }
      if (data.job && data.job.active) {
        setPollingThumbs(true);
      } else {
        setPollingThumbs(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    let timer: any = null;
    if (pollingThumbs) {
      timer = setTimeout(() => {
        loadThumbs(false);
      }, 1500);
    }
    return () => clearTimeout(timer);
  }, [pollingThumbs, thumbState]);

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

  // Actions
  const handleRegenArtwork = async () => {
    showToast('Generiere neues Lithen Green-Night Artwork...');
    try {
      await regenerateArtwork(project.name);
      showToast('Neues Artwork gespeichert & gesichert');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Fehler beim Bildwechsel');
    }
  };

  const handleCopyPromptAndOpenGemini = async () => {
    if (project.prompt_text) {
      try {
        await navigator.clipboard.writeText(project.prompt_text);
        showToast('Prompt in Zwischenablage kopiert!');
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
    showToast('Render-Pipeline gestartet...');
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
      await generateThumbnails(project.name, artistInput.trim(), 4);
      showToast('Thumbnail-Generierung gestartet...');
      setPollingThumbs(true);
      loadThumbs(false);
    } catch (e: any) {
      alert(e.message || 'Fehler');
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
  const mainVideoUrl = `/projects/${project.name}/final_youtube_video.mp4?t=${project.updated_at || 0}`;
  const shortVideoUrl = `/projects/${project.name}/short_reel_video.mp4?t=${project.updated_at || 0}`;
  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

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

      {/* HERO BEAT HEADER & AUDIO PLAYER */}
      <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 shadow-xl flex flex-col md:flex-row gap-6 items-start md:items-center">
        {/* Cover Preview (140x140) */}
        <div className="relative group w-36 h-36 rounded-xl overflow-hidden bg-black border border-white/[0.1] flex-shrink-0 shadow-lg">
          {project.has_artwork ? (
            <img
              src={`/projects/${project.name}/artwork.jpg?t=${project.updated_at || 0}`}
              alt={project.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-zinc-900 text-zinc-600">
              <ImageIcon className="w-8 h-8" />
            </div>
          )}
          <button
            onClick={handleRegenArtwork}
            className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1 text-[11px] font-semibold text-white"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>Bild wechseln</span>
          </button>
        </div>

        {/* Info & Player */}
        <div className="flex-1 flex flex-col gap-3.5 w-full min-w-0">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-black tracking-wide text-white uppercase">
                {project.name}
              </h1>
              {project.bpm && project.key && (
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30">
                  {project.bpm} BPM · {project.key}
                </span>
              )}
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
              <span>1440p YouTube: <strong className="text-zinc-200">{renderJob?.main_percent || 0}%</strong></span>
              <span>Short / Reel: <strong className="text-zinc-200">{renderJob?.short_percent || 0}%</strong></span>
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
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>Lithen Green-Night Artwork</span>
              </h2>
              <button
                onClick={handleRegenArtwork}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Neues Bild generieren</span>
              </button>
            </div>

            <div className="aspect-video rounded-xl overflow-hidden bg-black border border-white/[0.08] relative group">
              <img
                src={`/projects/${project.name}/artwork.jpg?t=${project.updated_at || 0}`}
                alt="Artwork"
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-3 left-3 bg-black/75 backdrop-blur-md px-3 py-1 rounded-md text-[11px] text-zinc-300 border border-white/10">
                1:1 Widescreen Grade · 2560x1440 Master
              </div>
            </div>

            <p className="text-xs text-zinc-400 leading-relaxed">
              Jedes Artwork durchläuft die Lithen Night-Cam Pipeline (Direct iPhone 15 Pro Flash, analoges Film-Korn, 1:1 Cover auf 16:9-Schwarzbalken). Nie wieder Copyright-Stress durch einzigartige Synthese.
            </p>
          </div>

          {/* Gemini Video-Loop Generator */}
          <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Video className="w-4 h-4 text-cyan-400" />
              <span>Gemini Video Loop</span>
            </h2>

            <p className="text-xs text-zinc-400 leading-relaxed">
              Kopiere den maßgeschneiderten Video-Prompt, öffne Gemini, lade die animierte Loop-MP4 herunter und ziehe sie direkt hier rein.
            </p>

            {/* Prompt Box */}
            <div className="bg-[#090a0f] border border-white/[0.08] rounded-xl p-3.5 relative">
              <div className="text-[11px] font-mono text-zinc-300 max-h-24 overflow-y-auto leading-relaxed">
                {project.prompt_text || 'Kein Prompt hinterlegt.'}
              </div>
            </div>

            <button
              onClick={handleCopyPromptAndOpenGemini}
              className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition-colors"
            >
              <Copy className="w-4 h-4" />
              <span>Prompt kopieren & Gemini öffnen</span>
              <ExternalLink className="w-3.5 h-3.5 opacity-70" />
            </button>

            {/* Video Loop Drop Zone */}
            <div
              onClick={() => loopInputRef.current?.click()}
              className="border-2 border-dashed border-white/[0.12] hover:border-cyan-500/50 rounded-2xl p-6 flex flex-col items-center justify-center gap-2.5 cursor-pointer bg-[#090a0f] transition-all"
            >
              {isUploadingLoop ? (
                <div className="flex flex-col items-center gap-2 py-2">
                  <Loader2 className="w-7 h-7 text-cyan-400 animate-spin" />
                  <span className="text-xs font-semibold text-white">Lade Video-Loop hoch...</span>
                </div>
              ) : (
                <>
                  <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                    <Upload className="w-5 h-5" />
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

                <div className="p-3 bg-[#090a0f] border border-white/[0.05] rounded-xl text-[11px] text-zinc-400 leading-relaxed">
                  💡 Animierte Typografie wird automatisch bei Sekunde 5 (`{project.key} · {project.bpm} BPM`) und Sekunde 10 (`listen full version now`) eingeblendet.
                </div>
              </div>

              {/* Render Action Buttons */}
              <div className="flex flex-col gap-2.5 pt-4 border-t border-white/[0.08]">
                <button
                  onClick={() => handleStartRender('both')}
                  disabled={isRendering || isJobActive}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-purple-500/20 flex items-center justify-center gap-2"
                >
                  <RefreshCw className={`w-4 h-4 ${isRendering || isJobActive ? 'animate-spin' : ''}`} />
                  <span>Beide neu rendern (1440p + Short)</span>
                </button>

                <button
                  onClick={() => handleStartRender('short_only')}
                  disabled={isRendering || isJobActive}
                  className="w-full py-2 px-4 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] disabled:opacity-50 text-zinc-200 text-xs font-semibold flex items-center justify-center gap-2"
                >
                  <Scissors className="w-4 h-4 text-purple-400" />
                  <span>Nur 9:16 Short neu schneiden</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: THUMBNAIL STUDIO */}
      {activeTab === 'thumbnails' && (
        <div className="bg-[#101118] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-cyan-400" />
                <span>YouTube Thumbnail Studio (Feed-Optimiert)</span>
              </h2>
              <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
                4:5 Hochformat zentriert auf schwarzem 16:9-Hintergrund (1280×720) ohne störenden Text – genau wie die reichweitenstärksten Type-Beat Kanäle. Klicke auf dein Lieblingsbild, um es festzulegen.
              </p>
            </div>

            {thumbState?.has_selected && (
              <a
                href={`/projects/${project.name}/thumbnail.jpg`}
                download={`${project.name}_thumbnail.jpg`}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-500/20"
              >
                <Download className="w-4 h-4" />
                <span>Ausgewähltes Thumbnail speichern</span>
              </a>
            )}
          </div>

          {/* Artist Tags Fast Selection */}
          {thumbState?.artists && thumbState.artists.length > 0 && (
            <div>
              <div className="text-[11px] font-semibold text-zinc-400 mb-1.5">Erkannte Artists aus den Metadaten:</div>
              <div className="flex flex-wrap gap-2">
                {thumbState.artists.map((a) => (
                  <button
                    key={a}
                    onClick={() => setArtistInput(a)}
                    className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                      artistInput === a
                        ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300 font-bold'
                        : 'bg-white/[0.04] border-white/[0.08] text-zinc-300 hover:border-white/20'
                    }`}
                  >
                    {a}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Prompt / Artist input row */}
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={artistInput}
              onChange={(e) => setArtistInput(e.target.value)}
              placeholder="Artist eingeben (z. B. Future x Drake, Metro Boomin, Travis Scott, Juice WRLD)..."
              className="flex-1 bg-[#090a0f] border border-white/[0.1] focus:border-cyan-500/50 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 outline-none"
            />
            <button
              onClick={handleGenerateThumbnails}
              disabled={isGeneratingThumbs || !!(thumbState?.job && thumbState.job.active)}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-cyan-500/20 flex items-center gap-2"
            >
              {thumbState?.job && thumbState.job.active ? (
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

          {/* Grid of Thumbnails */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {thumbState?.variants.map((v) => {
              const isSelected = thumbState.selected_src === v;
              return (
                <div
                  key={v}
                  onClick={() => handleSelectThumbnail(v)}
                  className={`p-2.5 rounded-2xl cursor-pointer transition-all duration-200 border-2 ${
                    isSelected
                      ? 'bg-emerald-500/10 border-emerald-500 shadow-xl shadow-emerald-500/10'
                      : 'bg-[#0d0e15] border-transparent hover:border-white/20'
                  }`}
                >
                  <div className="relative aspect-video rounded-xl overflow-hidden bg-black">
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
                      <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/85 text-white text-[10px] font-semibold">
                        {project.duration_str}
                      </div>
                    )}
                  </div>

                  <div className="mt-2.5">
                    <div className="text-xs font-semibold text-zinc-200 line-clamp-2 leading-snug">
                      [FREE] {artistInput || 'Type'} Type Beat 2026 - "{project.name.toUpperCase()}"
                    </div>
                    <div className="text-[11px] text-zinc-500 mt-1">
                      prodbyJMD · Vorschau im Feed
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
