export interface RenderJob {
  project: string;
  active: boolean;
  mode?: string;
  stage?: string;
  stage_label?: string;
  percent: number;
  main_percent?: number;
  short_percent?: number;
  current_time_str?: string;
  speed?: string;
  eta_str?: string;
  started_at?: number;
  finished_at?: number | null;
  error?: string | null;
}

export interface Project {
  id?: number;
  name: string;
  bpm: number;
  key: string;
  vibe?: string;
  duration_sec: number;
  duration_str: string;
  drop_sec: number;
  created_at?: number;
  updated_at?: number;
  is_completed: boolean | number;
  is_backed_up: boolean | number;
  has_mp3: boolean | number;
  has_artwork: boolean | number;
  has_video_loop: boolean | number;
  has_final_video: boolean | number;
  has_short_video: boolean | number;
  has_thumbnail: boolean | number;
  has_metadata: boolean | number;
  render_job?: RenderJob | null;
  prompt_text?: string;
  metadata_text?: string;
}

export interface AppConfig {
  gdrive_path: string;
  gemini_api_key: string;
  hf_api_key: string;
  used_artwork_hashes?: string[];
  completed_projects?: string[];
}

export interface ThumbnailState {
  artists: string[];
  titles: string[];
  default_artist: string;
  variants: string[];
  has_selected: boolean;
  selected_src: string;
  job?: {
    active: boolean;
    artist: string;
    total: number;
    done: number;
    failed: number;
    label: string;
    new_files: string[];
  } | null;
}
