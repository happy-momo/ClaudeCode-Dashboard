import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';

interface ImportSkillModalProps {
  open: boolean;
  onClose: () => void;
  onImport: (data: { name: string; content: string; scope: 'project' | 'global'; format: string }) => void;
}

const SKILL_TEMPLATES: Record<string, { name: string; content: string }> = {
  blank: {
    name: '',
    content: `---
name: my-skill
description: A custom skill for Claude Code
allowed-tools:
  - Read
  - Bash
metadata:
  trigger: my trigger phrase
---

# My Skill

Instructions for this skill...
`,
  },
  code_review: {
    name: 'code-review',
    content: `---
name: code-review
description: Review code for bugs, style issues, and improvements
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  trigger: code review, check code, review PR
---

# Code Review Skill

When reviewing code, follow these steps:

1. **Check for potential bugs and logic errors**
   - Look for null/undefined handling issues
   - Check boundary conditions
   - Verify loop termination conditions

2. **Verify proper error handling**
   - Make sure all possible errors are caught
   - Error messages should be clear and actionable

3. **Review naming conventions and code style**
   - Variable, function, class naming follows conventions
   - Consistent code formatting

4. **Look for performance concerns**
   - Find unnecessary loops or repeated calculations
   - Evaluate algorithm complexity

5. **Suggest improvements with specific examples**

Always provide constructive feedback with actionable suggestions.
`,
  },
  code_generation: {
    name: 'code-generation',
    content: `---
name: code-generation
description: Generate high-quality code following best practices
allowed-tools:
  - Read
  - Write
  - Edit
metadata:
  trigger: generate code, write code, create file
---

# Code Generation Skill

When generating code:

1. **Follow the existing code style and patterns**
   - Use naming conventions consistent with the project
   - Maintain the same code format and indentation

2. **Include proper type annotations**
   - Add types for function parameters and return values
   - Use appropriate type hints

3. **Add error handling for edge cases**
   - Handle boundary cases and exceptions
   - Provide meaningful error messages

4. **Write clean, readable code with clear variable names**
   - Keep functions concise with single responsibility
   - Avoid overly complex logic

5. **Include necessary imports and dependencies**
   - Add all required import statements
   - Ensure dependencies are properly declared

6. **Add comments for complex logic**
   - Provide explanations for complex logic
   - Document key algorithm steps
`,
  },
  custom_command: {
    name: 'custom-command',
    content: `---
name: custom-command
description: A custom command skill for Claude Code
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
metadata:
  trigger: run custom command, execute action
---

# Custom Command

This skill defines a custom command behavior.

## Trigger
When the user asks to run this specific command.

## Behavior

### Step 1: Parse the user's request
- Understand what operation the user wants to perform
- Confirm necessary parameters and options
- Validate input legitimacy

### Step 2: Execute the appropriate action
- Execute the command based on parsing results
- Handle possible errors and exceptions
- Log operations

### Step 3: Format the response clearly
- Display operation results
- Provide relevant output information
- Give next step suggestions

## Output Format

\`\`\`
✅ Operation Complete

Action performed: ...
Result: ...
Details: ...
\`\`\`
`,
  },
};

export function ImportSkillModal({ open, onClose, onImport }: ImportSkillModalProps) {
  const [template, setTemplate] = useState('blank');
  const [name, setName] = useState('');
  const [content, setContent] = useState(SKILL_TEMPLATES.blank.content);
  const [scope, setScope] = useState<'project' | 'global'>('project');

  const handleTemplateChange = (t: string) => {
    setTemplate(t);
    setContent(SKILL_TEMPLATES[t].content);
    setName(SKILL_TEMPLATES[t].name);
  };

  const handleSubmit = () => {
    if (!name.trim() || !content.trim()) return;
    onImport({ name: name.trim(), content, scope, format: 'frontmatter' });
    onClose();
  };

  return (
    <Modal open={open} onClose={onClose} title="Import Skill" className="max-w-2xl">
      <div className="space-y-4">
        {/* Template selector */}
        <div>
          <label className="text-xs font-medium text-anthro-text-muted uppercase tracking-wide mb-1 block">
            Template
          </label>
          <select
            value={template}
            onChange={(e) => handleTemplateChange(e.target.value)}
            className="w-full px-3 py-2 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-heading text-sm focus:outline-none focus:ring-2 focus:ring-anthro-accent/30"
          >
            <option value="blank">Blank Skill</option>
            <option value="code_review">Code Review</option>
            <option value="code_generation">Code Generation</option>
            <option value="custom_command">Custom Command</option>
          </select>
        </div>

        {/* Name */}
        <div>
          <label className="text-xs font-medium text-anthro-text-muted uppercase tracking-wide mb-1 block">
            Skill Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., my-custom-skill"
            className="w-full px-3 py-2 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-heading text-sm placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent"
          />
        </div>

        {/* Scope */}
        <div>
          <label className="text-xs font-medium text-anthro-text-muted uppercase tracking-wide mb-1 block">
            Scope
          </label>
          <div className="flex gap-3">
            <button
              className={`px-4 py-1.5 rounded-lg text-sm border transition-colors ${
                scope === 'project'
                  ? 'bg-anthro-accent text-white border-anthro-accent'
                  : 'bg-anthro-surface text-anthro-text-body border-anthro-border hover:bg-anthro-hover'
              }`}
              onClick={() => setScope('project')}
            >
              Project
            </button>
            <button
              className={`px-4 py-1.5 rounded-lg text-sm border transition-colors ${
                scope === 'global'
                  ? 'bg-anthro-accent text-white border-anthro-accent'
                  : 'bg-anthro-surface text-anthro-text-body border-anthro-border hover:bg-anthro-hover'
              }`}
              onClick={() => setScope('global')}
            >
              Global
            </button>
          </div>
        </div>

        {/* Content */}
        <div>
          <label className="text-xs font-medium text-anthro-text-muted uppercase tracking-wide mb-1 block">
            Content (Markdown with YAML frontmatter)
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={12}
            className="w-full px-3 py-2 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-heading text-sm font-mono placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent resize-y"
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" size="md" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleSubmit}
            disabled={!name.trim() || !content.trim()}
          >
            Import Skill
          </Button>
        </div>
      </div>
    </Modal>
  );
}
