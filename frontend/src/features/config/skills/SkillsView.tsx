import { useState, useMemo } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/Modal';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { EmptyState } from '@/components/ui/EmptyState';
import { SkillForm } from './SkillForm';
import { Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useSkills, useDeleteSkill, useCreateSkill } from './hooks';

const SKILLS_PER_PAGE = 5;
const SKILL_LIST_HEIGHT = '380px'; // Fixed height for 5 skill cards with pagination - matches PluginsView
const SKILL_CARD_MIN_HEIGHT = '72px'; // Fixed min height for consistent layout

function SkillCard({
  name,
  description,
  overridden,
  onDelete,
}: {
  name: string;
  description: string;
  overridden?: Record<string, unknown> | null;
  onDelete: () => void;
}) {
  const isOverridden = overridden != null;

  return (
    <div
      className={`flex justify-between items-start p-4 border rounded-xl ${
        isOverridden
          ? 'border-[#EFDACD] bg-[#F9EFEA]/40'
          : 'border-anthro-border hover:bg-anthro-bg'
      }`}
      style={{ minHeight: SKILL_CARD_MIN_HEIGHT }}
    >
      <div className="flex-1 min-w-0">
        <div className="font-medium text-anthro-text-heading text-sm flex items-center gap-2">
          <span className="truncate max-w-[180px] sm:max-w-[240px]">{name}</span>
          {isOverridden && (
            <span className="text-[10px] uppercase bg-[#EFDACD] text-[#B55A30] px-2 py-0.5 rounded font-bold tracking-widest shrink-0">
              Overridden
            </span>
          )}
        </div>
        <div className="text-sm text-anthro-text-body mt-1 truncate max-w-[280px] sm:max-w-[400px]">{description}</div>
      </div>
      <div className="flex items-center gap-2 ml-3 shrink-0">
        <button
          className="p-1.5 text-anthro-text-muted hover:text-red-500 hover:bg-red-50 rounded-lg"
          title="Delete skill"
          onClick={onDelete}
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

export function SkillsView() {
  const { data: projectSkills, isLoading: projectLoading, error: projectError } = useSkills('project');
  const { data: globalSkills, isLoading: globalLoading, error: globalError } = useSkills('global');
  const deleteMutation = useDeleteSkill();
  const createMutation = useCreateSkill();

  const [showNewSkill, setShowNewSkill] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ name: string; scope: string } | null>(null);
  const [projectPage, setProjectPage] = useState(1);
  const [globalPage, setGlobalPage] = useState(1);

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate({ name: deleteTarget.name, scope: deleteTarget.scope });
    setDeleteTarget(null);
  };

  // Pagination for project skills
  const projectSkillsPaginated = useMemo(() => {
    if (!projectSkills) return [];
    const start = (projectPage - 1) * SKILLS_PER_PAGE;
    return projectSkills.slice(start, start + SKILLS_PER_PAGE);
  }, [projectSkills, projectPage]);

  const projectTotalPages = Math.max(1, Math.ceil((projectSkills?.length || 0) / SKILLS_PER_PAGE));

  // Pagination for global skills
  const globalSkillsPaginated = useMemo(() => {
    if (!globalSkills) return [];
    const start = (globalPage - 1) * SKILLS_PER_PAGE;
    return globalSkills.slice(start, start + SKILLS_PER_PAGE);
  }, [globalSkills, globalPage]);

  const globalTotalPages = Math.max(1, Math.ceil((globalSkills?.length || 0) / SKILLS_PER_PAGE));

  if (projectLoading || globalLoading) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <LoadingSpinner message="Loading skills..." />
      </Card>
    );
  }

  if (projectError || globalError) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <ErrorDisplay
          message="Failed to load skills"
          details={projectError?.message || globalError?.message}
        />
      </Card>
    );
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-700">
      <div className="flex justify-between items-center shrink-0">
        <p className="text-sm font-medium text-anthro-text-body">
          Manage natural language interaction rules.
        </p>
        <Button variant="primary" size="md" onClick={() => setShowNewSkill(true)} className="transition-all duration-200">
          <Plus className="w-4 h-4 mr-2" /> New Skill
        </Button>
      </div>

      {/* Skills Grid - two columns with fixed height and pagination */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Project Skills Column */}
        <Card>
          <h3 className="text-lg font-serif text-anthro-text-heading mb-1 flex items-center">
            <div className="w-2.5 h-2.5 rounded-full bg-[#2C5F43] mr-3" />
            Project-Level Skills
          </h3>
          <p className="text-xs text-anthro-text-muted mb-3 font-mono bg-anthro-bg px-2 py-1 rounded inline-block">
            ./.claude/skills/
          </p>
          <div className="space-y-3" style={{ height: SKILL_LIST_HEIGHT, overflowY: 'auto' }}>
            {!projectSkills || projectSkills.length === 0 ? (
              <EmptyState
                title="No project skills"
                description="Add project-specific skills to customize Claude's behavior for this project."
              />
            ) : (
              projectSkillsPaginated.map((skill) => (
                <div key={skill.name}>
                  <SkillCard
                    name={skill.name}
                    description={skill.description}
                    overridden={skill.overridden ?? null}
                    onDelete={() => { setDeleteTarget({ name: skill.name, scope: skill.scope }); }}
                  />
                </div>
              ))
            )}
          </div>
          {/* Pagination for Project Skills */}
          {projectTotalPages > 1 && (
            <div className="flex justify-between items-center mt-3 pt-3 border-t border-anthro-border">
              <p className="text-xs text-anthro-text-muted">
                Page {projectPage} of {projectTotalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setProjectPage((p) => Math.max(1, p - 1))}
                  disabled={projectPage === 1}
                >
                  <ChevronLeft className="w-3 h-3 mr-0.5" />
                  Prev
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setProjectPage((p) => Math.min(projectTotalPages, p + 1))}
                  disabled={projectPage === projectTotalPages}
                >
                  Next
                  <ChevronRight className="w-3 h-3 ml-0.5" />
                </Button>
              </div>
            </div>
          )}
        </Card>

        {/* Global Skills Column */}
        <Card>
          <h3 className="text-lg font-serif text-anthro-text-heading mb-1 flex items-center">
            <div className="w-2.5 h-2.5 rounded-full bg-[#2D5B8A] mr-3" />
            Global Skills
          </h3>
          <p className="text-xs text-anthro-text-muted mb-3 font-mono bg-anthro-bg px-2 py-1 rounded inline-block">
            ~/.claude/skills/
          </p>
          <div className="space-y-3" style={{ height: SKILL_LIST_HEIGHT, overflowY: 'auto' }}>
            {!globalSkills || globalSkills.length === 0 ? (
              <EmptyState
                title="No global skills"
                description="Add global skills to customize Claude's behavior across all projects."
              />
            ) : (
              globalSkillsPaginated.map((skill) => (
                <div key={skill.name}>
                  <SkillCard
                    name={skill.name}
                    description={skill.description}
                    overridden={skill.overridden ?? null}
                    onDelete={() => { setDeleteTarget({ name: skill.name, scope: skill.scope }); }}
                  />
                </div>
              ))
            )}
          </div>
          {/* Pagination for Global Skills */}
          {globalTotalPages > 1 && (
            <div className="flex justify-between items-center mt-3 pt-3 border-t border-anthro-border">
              <p className="text-xs text-anthro-text-muted">
                Page {globalPage} of {globalTotalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setGlobalPage((p) => Math.max(1, p - 1))}
                  disabled={globalPage === 1}
                >
                  <ChevronLeft className="w-3 h-3 mr-0.5" />
                  Prev
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setGlobalPage((p) => Math.min(globalTotalPages, p + 1))}
                  disabled={globalPage === globalTotalPages}
                >
                  Next
                  <ChevronRight className="w-3 h-3 ml-0.5" />
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* New Skill Modal */}
      <Modal open={showNewSkill} onClose={() => setShowNewSkill(false)} title="Create New Skill">
        <SkillForm
          onSubmit={(data) => {
            createMutation.mutate(data);
            setShowNewSkill(false);
          }}
          onCancel={() => setShowNewSkill(false)}
        />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Skill"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
      />
    </div>
  );
}
