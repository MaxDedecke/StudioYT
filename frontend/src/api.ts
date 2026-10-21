import type { Project, AppConfig, ThumbnailState, RenderJob } from './types';

const BASE_URL = '';

export async function getProjects(includeCompleted = false): Promise<Project[]> {
  const res = await fetch(`${BASE_URL}/api/projects?include_completed=${includeCompleted}`);
  if (!res.ok) throw new Error('Fehler beim Laden der Projekte');
  return res.json();
}

export async function uploadMp3(file: File, name?: string): Promise<{ success: boolean; project: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const query = name ? `?name=${encodeURIComponent(name)}` : '';
  const res = await fetch(`${BASE_URL}/api/upload_mp3${query}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Fehler beim Hochladen der MP3');
  return res.json();
}

export async function uploadVideoLoop(project: string, file: File): Promise<{ success: boolean; job: RenderJob }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/api/upload_video?project=${encodeURIComponent(project)}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Fehler beim Hochladen des Video-Loops');
  return res.json();
}

export async function completeProject(project: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/complete_project`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project }),
  });
  if (!res.ok) throw new Error('Fehler beim Abschließen des Projekts');
}

export async function updateBeatAudio(
  project: string,
  bpm: number,
  key: string,
  sync_metadata = true
): Promise<{ success: boolean; project: string; bpm: number; key: string; metadata_text?: string }> {
  const res = await fetch(`${BASE_URL}/api/update_beat_audio`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, bpm, key, sync_metadata }),
  });
  if (!res.ok) throw new Error('Fehler beim Aktualisieren der Beat-Daten');
  return res.json();
}

export async function deleteProject(project: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/delete_project`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project }),
  });
  if (!res.ok) throw new Error('Fehler beim Löschen des Projekts');
}

export async function regenerateArtwork(project: string): Promise<{ success: boolean; prompt_text: string }> {
  const res = await fetch(`${BASE_URL}/api/regenerate_artwork`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project }),
  });
  if (!res.ok) throw new Error('Fehler beim Neugenerieren des Artworks');
  return res.json();
}

export async function analyzeArtwork(project: string): Promise<{ success: boolean; prompt_text: string }> {
  const res = await fetch(`${BASE_URL}/api/analyze_artwork`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project }),
  });
  if (!res.ok) throw new Error('Fehler bei der Bild-Analyse');
  return res.json();
}

export async function triggerRender(project: string, mode = 'both', short_start?: number, short_duration = 30): Promise<{ success: boolean; job: RenderJob }> {
  const res = await fetch(`${BASE_URL}/api/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, mode, short_start, short_duration }),
  });
  if (!res.ok) throw new Error('Fehler beim Starten des Renderings');
  return res.json();
}

export async function getRenderStatus(): Promise<{ active_any: boolean; jobs: Record<string, RenderJob> }> {
  const res = await fetch(`${BASE_URL}/api/render_status`);
  if (!res.ok) throw new Error('Fehler beim Abrufen des Render-Status');
  return res.json();
}

export async function regenerateMetadata(project: string): Promise<{ success: boolean; metadata_text: string }> {
  const res = await fetch(`${BASE_URL}/api/regenerate_metadata`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project }),
  });
  if (!res.ok) throw new Error('Fehler beim Neugenerieren der Metadaten');
  return res.json();
}

export async function saveMetadata(project: string, metadata_text: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/save_metadata`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, metadata_text }),
  });
  if (!res.ok) throw new Error('Fehler beim Speichern der Metadaten');
}

export async function getThumbnails(project: string): Promise<ThumbnailState> {
  const res = await fetch(`${BASE_URL}/api/thumbnails?project=${encodeURIComponent(project)}`);
  if (!res.ok) throw new Error('Fehler beim Abrufen der Thumbnails');
  return res.json();
}

export async function generateThumbnails(project: string, brand_tag = 'prodbyjmd', _count?: number): Promise<{ success: boolean; brand_tag: string; variants: string[] }> {
  const res = await fetch(`${BASE_URL}/api/generate_thumbnails`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, brand_tag }),
  });
  if (!res.ok) throw new Error('Fehler beim Generieren der Brand-Thumbnails');
  return res.json();
}

export async function selectThumbnail(project: string, file: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/select_thumbnail`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, file }),
  });
  if (!res.ok) throw new Error('Fehler beim Auswählen des Thumbnails');
}

export async function getConfig(): Promise<AppConfig> {
  const res = await fetch(`${BASE_URL}/api/config`);
  if (!res.ok) throw new Error('Fehler beim Laden der Einstellungen');
  return res.json();
}

export async function updateConfig(cfg: Partial<AppConfig>): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg),
  });
  if (!res.ok) throw new Error('Fehler beim Speichern der Einstellungen');
}

export async function syncDrive(project?: string): Promise<{ success: boolean; result: any }> {
  const res = await fetch(`${BASE_URL}/api/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project }),
  });
  if (!res.ok) throw new Error('Fehler beim Synchronisieren');
  return res.json();
}

export async function openExplorerFolder(project = ''): Promise<void> {
  await fetch(`${BASE_URL}/api/open_folder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project }),
  });
}
