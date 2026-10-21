import React, { useState, useRef } from 'react';
import {
  Play,
  Pause,
  Cloud,
  Folder,
  Check,
  X,
  Sparkles,
  Image as ImageIcon,
  Video,
  FileText,
  Upload,
  ChevronDown,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import type { Project } from '../types';
import { openExplorerFolder } from '../api';

interface ProjectCardProps {
  project: Project;
  onOpenThumbnails: (project: Project) => void;
  onOpenMetadata: (project: Project) => void;
  onOpenVideo: (project: Project, type: 'main' | 'short') => void;
  onTriggerRender: (projectName: string, mode: 'both' | 'main_only' | 'short_only') => void;
  onRegenerateArtwork: (projectName: string) => void;
  onComplete: (projectName: string) => void;
  onDelete: (projectName: string) => void;
  onUploadVideoLoop: (projectName: string, file: File) => void;
  showToast: (msg: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onOpenThumbnails,
  onOpenMetadata,
  onOpenVideo,
  onTriggerRender,
  onRegenerateArtwork,
  onComplete,
  onDelete,
  onUploadVideoLoop,
  showToast,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(project.duration_sec || 0);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [geminiClicked, setGeminiClicked] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const videoInputRef = useRef<HTMLInputElement | null>(null);

  const job = project.render_job;
  const isRendering = !!(job && job.active);
  const anyVideoReady = !!(project.has_final_video || project.has_short_video);
  const bothVideosReady = !!(project.has_final_video && project.has_short_video);

  const todoGemini = !isRendering && !project.has_video_loop && !anyVideoReady && !geminiClicked;
  const todoLoop = !isRendering && !project.has_video_loop && !anyVideoReady && geminiClicked;
  const todoRenderMain = !isRendering && project.has_video_loop && !project.has_final_video;
  const todoRenderShort = !isRendering && project.has_final_video && !project.has_short_video;
  const todoTexte = !isRendering && bothVideosReady;

  let stepLabel = 'Steps';
  if (isRendering) stepLabel = 'Rendert...';
  else if (todoGemini) stepLabel = 'Gemini öffnen';
  else if (todoLoop) stepLabel = 'Loop laden';
  else if (todoRenderMain) stepLabel = '1440p Video';
  else if (todoRenderShort) stepLabel = 'Short / Reel';
  else if (todoTexte) stepLabel = 'Videos & Texte';

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
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    const targetTime = ratio * duration;
    audioRef.current.currentTime = targetTime;
    setCurrentTime(targetTime);
  };

  const openGemini = async () => {
    setGeminiClicked(true);
    if (project.prompt_text) {
      try {
        await navigator.clipboard.writeText(project.prompt_text);
        showToast('Prompt kopiert & Gemini geöffnet');
      } catch (e) {
        console.error(e);
      }
    }
    window.open('https://gemini.google.com/app', '_blank');
  };

  const formatSec = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = Math.floor(s % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="bg-[#101118] border border-white/[0.07] hover:border-white/[0.12] rounded-2xl p-4 transition-all duration-200 flex flex-col md:flex-row gap-5 shadow-lg shadow-black/40 relative">
      {/* Hidden file input for loop video upload */}
      <input
        type="file"
        ref={videoInputRef}
        accept="video/mp4"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            onUploadVideoLoop(project.name, e.target.files[0]);
          }
        }}
      />

      {/* LEFT: ARTWORK & OVERLAY ACTIONS */}
      <div className="relative group w-full md:w-36 h-36 flex-shrink-0 rounded-xl overflow-hidden bg-black border border-white/[0.08]">
        {project.has_artwork ? (
          <img
            src={`/projects/${project.name}/artwork.jpg?t=${project.updated_at || 0}`}
            alt={project.name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-600 bg-zinc-900">
            <ImageIcon className="w-8 h-8 opacity-40" />
          </div>
        )}

        {/* Hover action pills */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-2 gap-1.5 backdrop-blur-[2px]">
          <button
            onClick={() => onRegenerateArtwork(project.name)}
            className="w-full py-1 px-2 rounded-md bg-white/10 hover:bg-white/20 border border-white/20 text-[10px] font-semibold text-white flex items-center justify-center gap-1 transition-colors"
          >
            <Sparkles className="w-3 h-3 text-purple-400" />
            <span>Bild wechseln</span>
          </button>
          <button
            onClick={() => onOpenThumbnails(project)}
            className="w-full py-1 px-2 rounded-md bg-white/10 hover:bg-white/20 border border-white/20 text-[10px] font-semibold text-white flex items-center justify-center gap-1 transition-colors"
          >
            <ImageIcon className="w-3 h-3 text-cyan-400" />
            <span>Thumbnail</span>
          </button>
        </div>
      </div>

      {/* RIGHT: PROJECT INFO, AUDIO SCRUBBER & WORKFLOW */}
      <div className="flex-1 flex flex-col justify-between gap-3 min-w-0">
        {/* Top Info Header */}
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-extrabold text-base tracking-wide text-white uppercase">
                {project.name}
              </h3>
              {project.bpm && project.key && (
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white/[0.06] text-zinc-300 border border-white/[0.08]">
                  {project.bpm} BPM · {project.key}
                </span>
              )}
              {project.is_backed_up ? (
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center gap-1">
                  <Cloud className="w-3 h-3" />
                  <span>Gesichert</span>
                </span>
              ) : null}
              {isRendering && (
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1 animate-pulse">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Rendert...</span>
                </span>
              )}
            </div>
            {project.vibe && (
              <p className="text-xs text-zinc-400 mt-1 line-clamp-1">{project.vibe}</p>
            )}
          </div>

          {/* Action & Steps Buttons */}
          <div className="flex items-center gap-2">
            {/* Steps dropdown */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                  todoGemini || todoLoop || todoRenderMain || todoRenderShort || todoTexte
                    ? 'bg-purple-600/20 hover:bg-purple-600/30 border-purple-500/40 text-purple-300'
                    : 'bg-white/[0.05] hover:bg-white/[0.1] border-white/[0.1] text-zinc-300'
                }`}
              >
                <span>{stepLabel}</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </button>

              {dropdownOpen && (
                <div
                  className="absolute right-0 mt-2 w-52 bg-[#141520] border border-white/[0.12] rounded-xl shadow-2xl p-1.5 z-50 flex flex-col gap-1 backdrop-blur-md"
                  onClick={() => setDropdownOpen(false)}
                >
                  <button
                    onClick={openGemini}
                    className="flex items-center justify-between px-3 py-2 text-xs rounded-lg hover:bg-white/[0.08] text-left text-zinc-200"
                  >
                    <span>1. Gemini öffnen</span>
                    <ExternalLink className="w-3 h-3 text-zinc-500" />
                  </button>
                  <button
                    onClick={() => videoInputRef.current?.click()}
                    className="flex items-center justify-between px-3 py-2 text-xs rounded-lg hover:bg-white/[0.08] text-left text-zinc-200"
                  >
                    <span>2. Loop laden</span>
                    <Upload className="w-3 h-3 text-zinc-500" />
                  </button>
                  {project.has_final_video ? (
                    <button
                      onClick={() => onOpenVideo(project, 'main')}
                      className="flex items-center justify-between px-3 py-2 text-xs rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 text-left font-medium"
                    >
                      <span>▶ 1440p Video</span>
                      <Video className="w-3 h-3" />
                    </button>
                  ) : (
                    <button
                      onClick={() => onTriggerRender(project.name, 'both')}
                      className="flex items-center justify-between px-3 py-2 text-xs rounded-lg hover:bg-white/[0.08] text-left text-zinc-300"
                    >
                      <span>3. 1440p Video rendern</span>
                      <Video className="w-3 h-3 text-zinc-500" />
                    </button>
                  )}
                  {project.has_short_video ? (
                    <button
                      onClick={() => onOpenVideo(project, 'short')}
                      className="flex items-center justify-between px-3 py-2 text-xs rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 text-left font-medium"
                    >
                      <span>▶ Short / Reel</span>
                      <Video className="w-3 h-3" />
                    </button>
                  ) : (
                    <button
                      onClick={() => onTriggerRender(project.name, 'short_only')}
                      className="flex items-center justify-between px-3 py-2 text-xs rounded-lg hover:bg-white/[0.08] text-left text-zinc-300"
                    >
                      <span>4. Short / Reel rendern</span>
                      <Video className="w-3 h-3 text-zinc-500" />
                    </button>
                  )}
                  <button
                    onClick={() => onOpenThumbnails(project)}
                    className={`flex items-center justify-between px-3 py-2 text-xs rounded-lg text-left font-medium ${
                      project.has_thumbnail
                        ? 'bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20'
                        : 'hover:bg-white/[0.08] text-zinc-300'
                    }`}
                  >
                    <span>{project.has_thumbnail ? '▶ Thumbnail' : '5. Thumbnail Studio'}</span>
                    <ImageIcon className="w-3 h-3 text-zinc-500" />
                  </button>
                  <button
                    onClick={() => onOpenMetadata(project)}
                    className="flex items-center justify-between px-3 py-2 text-xs rounded-lg hover:bg-white/[0.08] text-left text-zinc-200"
                  >
                    <span>6. Texte & SEO</span>
                    <FileText className="w-3 h-3 text-zinc-500" />
                  </button>
                </div>
              )}
            </div>

            {/* Quick folder button */}
            <button
              onClick={() => openExplorerFolder(project.name)}
              title="Projektordner öffnen"
              className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-zinc-400 hover:text-white transition-colors"
            >
              <Folder className="w-4 h-4" />
            </button>

            {/* Complete beat button */}
            {anyVideoReady && (
              <button
                onClick={() => onComplete(project.name)}
                title="Beat abschließen & ins Archiv schieben"
                className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 transition-colors"
              >
                <Check className="w-4 h-4" />
              </button>
            )}

            {/* Delete button */}
            <button
              onClick={() => onDelete(project.name)}
              title="Aus Dashboard entfernen"
              className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* LIVE RENDER MONITOR (Visible when rendering) */}
        {isRendering && (
          <div className="bg-[#0b0c13] border border-amber-500/30 rounded-xl p-3 my-1">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {job?.stage_label || 'Rendere...'}
              </span>
              <span className="font-bold text-white">{job?.percent || 0}%</span>
            </div>
            {/* Progress bar track */}
            <div className="w-full bg-white/[0.08] rounded-full h-2 overflow-hidden mb-2">
              <div
                className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${job?.percent || 0}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-zinc-400">
              <div className="flex gap-3">
                <span>1440p: <strong className="text-zinc-200">{job?.main_percent || 0}%</strong></span>
                <span>Short: <strong className="text-zinc-200">{job?.short_percent || 0}%</strong></span>
              </div>
              <div>
                {job?.current_time_str} · {job?.speed} · {job?.eta_str}
              </div>
            </div>
          </div>
        )}

        {/* AUDIO PLAYER & SCRUBBER */}
        {project.has_mp3 ? (
          <div className="flex items-center gap-3 bg-[#0d0e15] border border-white/[0.05] p-2.5 rounded-xl">
            <button
              onClick={togglePlay}
              className="w-8 h-8 rounded-full bg-white/[0.08] hover:bg-white/[0.15] text-white flex items-center justify-center transition-colors flex-shrink-0"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current ml-0.5" />}
            </button>

            {/* Scrubber track */}
            <div
              onClick={handleSeek}
              className="flex-1 h-3 flex items-center cursor-pointer group"
            >
              <div className="w-full bg-white/[0.08] h-1.5 rounded-full overflow-hidden group-hover:h-2 transition-all">
                <div
                  className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            <div className="text-[11px] text-zinc-400 font-mono flex-shrink-0">
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
        ) : null}
      </div>
    </div>
  );
};
