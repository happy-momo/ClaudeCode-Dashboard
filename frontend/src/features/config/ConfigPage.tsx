import { Tabs } from '@/components/ui/Tabs';
import { useState } from 'react';
import { EffectiveView } from './effective/EffectiveView';
import { SkillsView } from './skills/SkillsView';
import { McpsView } from './mcps/McpsView';
import { PluginsView } from './plugins/PluginsView';

const subTabs = [
  { id: 'effective', label: 'Unified View' },
  { id: 'skills', label: 'Skills' },
  { id: 'mcps', label: 'MCP Servers' },
  { id: 'plugins', label: 'Plugins' },
];

export function ConfigPage() {
  const [subTab, setSubTab] = useState('effective');

  return (
    <div className="space-y-4 animate-in fade-in duration-700">
      <div className="shrink-0">
        <h2 className="text-3xl font-serif text-anthro-text-heading tracking-tight">Capability Management</h2>
        <p className="text-anthro-text-body text-sm mt-1 font-medium">
          Manage Global and Project-level Skills, MCPs, and Plugins with scope priority.
        </p>
      </div>

      <Tabs items={subTabs} activeId={subTab} onChange={setSubTab} />

      <div className="pt-2">
        {subTab === 'effective' && <EffectiveView />}
        {subTab === 'skills' && <SkillsView />}
        {subTab === 'mcps' && <McpsView />}
        {subTab === 'plugins' && <PluginsView />}
      </div>
    </div>
  );
}
