import React, { useState, useRef } from 'react';
import {
  Play,
  Pause,
  Cloud,
  Folder,
  Check,
  X,
  Sparkles,
  Video,
  FileText,
  Image as ImageIcon,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import type { Project } from '../types';
import { openExplorerFolder } from '../api';

interface ProjectCardProps {
  project: Project;
  onSelectBeat: (project: Project) => void;
  onComplete: (projectName: string) => void;
  onDelete: (projectName: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onSelectBeat,
  onComplete,
  onDelete,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const job = project.render_job;
  const isRendering = !!(job && job.active);

  const togglePlay = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  return (
    <div
      onClick={() => onSelectBeat(project)}
      className="group bg-[#101118] border border-white/[0.07] hover:border-purple-500/40 rounded-2xl p-4 transition-all duration-200 cursor-pointer shadow-lg shadow-black/40 hover:shadow-purple-500/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
    >
      {/* Audio element */}
      {project.has_mp3 && (
        <audio
          ref={audioRef}
          src={`/projects/${project.name}/beat.mp3`}
          onEnded={() => setIsPlaying(false)}
        />
      )}

      {/* LEFT: Cover + Play Overlay + Info */}
      <div className="flex items-center gap-4 min-w-0">
        <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-black border border-white/[0.1] flex-shrink-0 group-hover:border-purple-500/50 transition-colors">
          {project.has_artwork ? (
            <img
              src={`/projects/${project.name}/artwork.jpg?t=${project.artwork_mtime || project.updated_at || 0}`}
              alt={project.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-zinc-900 text-zinc-600">
              <ImageIcon className="w-6 h-6" />
            </div>
          )}

          {/* Quick Play Trigger */}
          {project.has_mp3 && (
            <button
              onClick={togglePlay}
              className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white"
            >
              {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
            </button>
          )}
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-extrabold text-base tracking-wide text-white group-hover:text-purple-300 transition-colors uppercase truncate">
              {project.name}
            </h3>
            {project.bpm && project.key && (
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white/[0.06] text-zinc-300 border border-white/[0.08]">
                {project.bpm} BPM · {project.key}
              </span>
            )}
            {project.is_backed_up ? (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center gap-1">
                <Cloud className="w-3 h-3" />
                <span>Drive</span>
              </span>
            ) : null}
            {isRendering && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1 animate-pulse">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Rendert {job?.percent || 0}%</span>
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-zinc-400 mt-1">
            <span>{project.duration_str || '--:--'}</span>
            {project.vibe && (
              <>
                <span className="text-zinc-600">·</span>
                <span className="truncate max-w-[280px] text-zinc-400">{project.vibe}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT: Status Checkmarks & Open Action */}
      <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end border-t sm:border-t-0 pt-2 sm:pt-0 border-white/[0.06]">
        {/* Status Indicators */}
        <div className="flex items-center gap-1.5 text-xs">
          <span
            title={project.has_artwork ? 'Artwork bereit' : 'Kein Artwork'}
            className={`p-1.5 rounded-lg border flex items-center gap-1 ${
              project.has_artwork ? 'bg-purple-500/10 border-purple-500/20 text-purple-300' : 'bg-white/[0.02] border-white/[0.05] text-zinc-600'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
          </span>

          <span
            title={project.has_final_video ? '1440p Video bereit' : '1440p Video fehlt'}
            className={`p-1.5 rounded-lg border flex items-center gap-1 ${
              project.has_final_video ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-white/[0.02] border-white/[0.05] text-zinc-600'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
          </span>

          <span
            title={project.has_thumbnail ? 'Thumbnail ausgewählt' : 'Kein Thumbnail'}
            className={`p-1.5 rounded-lg border flex items-center gap-1 ${
              project.has_thumbnail ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400' : 'bg-white/[0.02] border-white/[0.05] text-zinc-600'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
          </span>

          <span
            title={project.has_metadata ? 'SEO Texte bereit' : 'Texte fehlen'}
            className={`p-1.5 rounded-lg border flex items-center gap-1 ${
              project.has_metadata ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 'bg-white/[0.02] border-white/[0.05] text-zinc-600'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={(e) => {
              e.stopPropagation();
              openExplorerFolder(project.name);
            }}
            title="Ordner öffnen"
            className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-zinc-400 hover:text-white"
          >
            <Folder className="w-4 h-4" />
          </button>

          {(project.has_final_video || project.has_short_video) && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onComplete(project.name);
              }}
              title="Abschließen"
              className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400"
            >
              <Check className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(project.name);
            }}
            title="Löschen"
            className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-purple-600/15 group-hover:bg-purple-600 group-hover:text-white text-purple-300 text-xs font-bold transition-all ml-1">
            <span>Öffnen</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>
      </div>
    </div>
  );
};
