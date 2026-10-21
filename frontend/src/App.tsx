import { useState, useEffect, useMemo } from 'react';
import type { Project } from './types';
import {
  getProjects,
  getRenderStatus,
  completeProject,
  deleteProject,
} from './api';
import { Navbar } from './components/Navbar';
import { FiltersBar } from './components/FiltersBar';
import { ProjectCard } from './components/ProjectCard';
import { BeatDetailPage } from './components/BeatDetailPage';
import { UploadModal } from './components/UploadModal';
import { SettingsModal } from './components/SettingsModal';
import { WorkflowModal } from './components/WorkflowModal';
import { Music2, Plus } from 'lucide-react';

export function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [search, setSearch] = useState('');
  const [selectedKey, setSelectedKey] = useState('');
  const [sortBy, setSortBy] = useState('recent');
  const [showCompleted, setShowCompleted] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Selected beat for the full-page workspace view
  const [selectedBeatName, setSelectedBeatName] = useState<string | null>(() => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('beat') || null;
  });

  // Global Modals
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isWorkflowOpen, setIsWorkflowOpen] = useState(false);

  const showToast = (msg: string) => {
    setToastMsg(msg);
  };

  useEffect(() => {
    if (toastMsg) {
      const timer = setTimeout(() => setToastMsg(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMsg]);

  // Sync selected beat with URL
  const handleSelectBeat = (project: Project) => {
    setSelectedBeatName(project.name);
    const url = new URL(window.location.href);
    url.searchParams.set('beat', project.name);
    window.history.pushState({}, '', url);
  };

  const handleBackToOverview = () => {
    setSelectedBeatName(null);
    const url = new URL(window.location.href);
    url.searchParams.delete('beat');
    window.history.pushState({}, '', url);
  };

  // Handle browser back button
  useEffect(() => {
    const onPopState = () => {
      const urlParams = new URLSearchParams(window.location.search);
      setSelectedBeatName(urlParams.get('beat') || null);
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  // Load projects
  const loadProjects = async () => {
    try {
      const data = await getProjects(showCompleted);
      setProjects(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadProjects();
  }, [showCompleted]);

  // Periodic polling for background render jobs
  useEffect(() => {
    let wasActive = false;
    const interval = setInterval(async () => {
      try {
        const status = await getRenderStatus();
        if (status.active_any) {
          wasActive = true;
          loadProjects();
        } else if (wasActive) {
          wasActive = false;
          loadProjects();
        }
      } catch (e) {
        // quiet
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [showCompleted]);

  // Extract distinct keys for filter dropdown
  const availableKeys = useMemo(() => {
    const keys = new Set<string>();
    projects.forEach((p) => {
      if (p.key) keys.add(p.key);
    });
    return Array.from(keys).sort();
  }, [projects]);

  // Filtered and sorted projects for the overview
  const filteredProjects = useMemo(() => {
    return projects
      .filter((p) => {
        const matchesSearch =
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          (p.vibe && p.vibe.toLowerCase().includes(search.toLowerCase())) ||
          (p.bpm && p.bpm.toString().includes(search)) ||
          (p.key && p.key.toLowerCase().includes(search.toLowerCase()));
        const matchesKey = !selectedKey || p.key === selectedKey;
        return matchesSearch && matchesKey;
      })
      .sort((a, b) => {
        if (sortBy === 'bpm_desc') return (b.bpm || 0) - (a.bpm || 0);
        if (sortBy === 'bpm_asc') return (a.bpm || 0) - (b.bpm || 0);
        if (sortBy === 'name') return a.name.localeCompare(b.name);
        return (b.updated_at || 0) - (a.updated_at || 0);
      });
  }, [projects, search, selectedKey, sortBy]);

  const activeRenderCount = projects.filter((p) => p.render_job && p.render_job.active).length;
  const currentProject = projects.find((p) => p.name === selectedBeatName);

  // Actions
  const handleComplete = async (projectName: string) => {
    try {
      await completeProject(projectName);
      showToast(`Beat "${projectName}" abgeschlossen`);
      loadProjects();
      if (selectedBeatName === projectName) {
        handleBackToOverview();
      }
    } catch (e: any) {
      alert(e.message || 'Fehler');
    }
  };

  const handleDelete = async (projectName: string) => {
    if (!window.confirm(`Beat "${projectName}" wirklich aus der Pipeline entfernen?`)) return;
    try {
      await deleteProject(projectName);
      showToast(`Beat "${projectName}" archiviert`);
      loadProjects();
      if (selectedBeatName === projectName) {
        handleBackToOverview();
      }
    } catch (e: any) {
      alert(e.message || 'Fehler');
    }
  };

  return (
    <div className="min-h-screen bg-[#090a0f] text-[#f4f4f5]">
      {/* Top Navbar */}
      <Navbar
        onOpenUpload={() => setIsUploadOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenWorkflow={() => setIsWorkflowOpen(true)}
        projectCount={projects.length}
        activeRenderCount={activeRenderCount}
      />

      {/* Main Content: Either Full Beat Detail Page or Overview List */}
      {selectedBeatName && currentProject ? (
        <BeatDetailPage
          project={currentProject}
          onBack={handleBackToOverview}
          onRefresh={loadProjects}
          onComplete={handleComplete}
          onDelete={handleDelete}
          showToast={showToast}
        />
      ) : (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
          {/* Filter & Search Toolbar */}
          <FiltersBar
            search={search}
            onSearchChange={setSearch}
            selectedKey={selectedKey}
            onKeyChange={setSelectedKey}
            sortBy={sortBy}
            onSortChange={setSortBy}
            showCompleted={showCompleted}
            onToggleCompleted={() => setShowCompleted(!showCompleted)}
            availableKeys={availableKeys}
          />

          {/* Project Cards List */}
          {filteredProjects.length === 0 ? (
            <div className="text-center py-24 bg-[#0d0e15] border border-white/[0.05] rounded-3xl p-8 flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-400 mb-4">
                <Music2 className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-white mb-1">
                {search || selectedKey ? 'Keine Beats gefunden' : 'Keine aktiven Beats in der Pipeline'}
              </h3>
              <p className="text-xs text-zinc-400 max-w-sm mb-5">
                {search || selectedKey
                  ? 'Versuche andere Suchbegriffe oder setze den Tonart-Filter zurück.'
                  : 'Lade deine MP3 aus FL Studio oder deiner DAW hoch, um Artworks, Videos und YouTube-Thumbnails zu erstellen.'}
              </p>
              <button
                onClick={() => setIsUploadOpen(true)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-500/20"
              >
                <Plus className="w-4 h-4" />
                <span>Ersten Beat hochladen</span>
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {filteredProjects.map((p) => (
                <ProjectCard
                  key={p.name}
                  project={p}
                  onSelectBeat={handleSelectBeat}
                  onComplete={handleComplete}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </main>
      )}

      {/* Global Modals */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        showToast={showToast}
        onUploadSuccess={loadProjects}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        showToast={showToast}
      />

      <WorkflowModal
        isOpen={isWorkflowOpen}
        onClose={() => setIsWorkflowOpen(false)}
      />

      {/* Toast Feedback */}
      {toastMsg && (
        <div className="fixed bottom-6 right-6 bg-white text-black font-semibold text-xs px-4 py-2.5 rounded-xl shadow-2xl z-50 flex items-center gap-2">
          <span>✓</span>
          <span>{toastMsg}</span>
        </div>
      )}
    </div>
  );
}

export default App;
