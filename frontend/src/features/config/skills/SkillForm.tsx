import { useState, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/Button';

const SKILL_TEMPLATES: Record<string, { name: string; description: string; content: string }> = {
  blank: {
    name: '',
    description: '',
    content: '',
  },
  code_review: {
    name: 'code-review',
    description: 'Review code for bugs, style issues, and improvements',
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

## 1. Check for potential bugs and logic errors
- Look for null/undefined handling issues
- Check boundary conditions
- Verify loop termination conditions
- Ensure exception handling is complete

## 2. Verify proper error handling
- Make sure all possible errors are caught
- Error messages should be clear and actionable
- Avoid silent failures

## 3. Review naming conventions and code style
- Variable, function, class naming follows conventions
- Consistent code formatting
- Clear and necessary comments

## 4. Look for performance concerns
- Find unnecessary loops or repeated calculations
- Check for memory leak risks
- Evaluate algorithm complexity

## 5. Suggest improvements
- Provide specific code examples
- Explain the reasoning for improvements
- Provide relevant documentation or references

## Output Format

Always provide constructive feedback with actionable suggestions.
`,
  },
  code_generation: {
    name: 'code-generation',
    description: 'Generate high-quality code following best practices',
    content: `---
name: code-generation
description: Generate high-quality code following best practices
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
metadata:
  trigger: generate code, write code, create file
---

# Code Generation Skill

When generating code:

## 1. Follow the existing code style and patterns
- Use naming conventions consistent with the project
- Maintain the same code format and indentation
- Follow the project's code organization patterns

## 2. Include proper type annotations
- Add types for function parameters and return values
- Use appropriate type hints
- Follow the language's type system best practices

## 3. Add error handling for edge cases
- Handle boundary cases and exceptions
- Provide meaningful error messages
- Use appropriate exception types

## 4. Write clean, readable code
- Use clear, descriptive variable names
- Keep functions concise with single responsibility
- Avoid overly complex logic

## 5. Include necessary imports and dependencies
- Add all required import statements
- Ensure dependencies are properly declared
- Check version compatibility

## 6. Add comments for complex logic
- Provide explanations for complex logic
- Document key algorithm steps
- Note any special considerations or trade-offs
`,
  },
  custom_command: {
    name: 'custom-command',
    description: 'A custom command skill for Claude Code',
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

# Custom Command Skill

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

interface SkillFormProps {
  onSubmit: (data: { name: string; description: string; content: string; scope: string }) => void;
  onCancel: () => void;
}

export function SkillForm({ onSubmit, onCancel }: SkillFormProps) {
  const [template, setTemplate] = useState('blank');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [scope, setScope] = useState<'project' | 'global'>('project');

  const handleTemplateChange = useCallback((t: string) => {
    setTemplate(t);
    const tmpl = SKILL_TEMPLATES[t];
    if (tmpl.name) setName(tmpl.name);
    if (tmpl.description) setDescription(tmpl.description);
    setContent(tmpl.content);
  }, []);

  const handleSubmit = useCallback((e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!name.trim() || !content.trim()) return;
    onSubmit({ name: name.trim(), description, content, scope });
  }, [name, description, content, scope, onSubmit]);

  const isSubmitDisabled = useMemo(() => !name.trim() || !content.trim(), [name, content]);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Template selector */}
      <div>
        <label className="block text-xs font-medium text-anthro-text-muted uppercase tracking-wide mb-1.5">
          Start from template
        </label>
        <select
          value={template}
          onChange={(e) => handleTemplateChange(e.target.value)}
          className="w-full px-3 py-2 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-heading text-sm focus:outline-none focus:ring-2 focus:ring-anthro-accent/30"
        >
          <option value="blank">Blank (start from scratch)</option>
          <option value="code_review">Code Review</option>
          <option value="code_generation">Code Generation</option>
          <option value="custom_command">Custom Command</option>
        </select>
      </div>

      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
          Skill Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="my-skill"
          className="w-full px-3 py-2 bg-anthro-surface border border-anthro-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted"
          required
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
          Description
        </label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of what this skill does"
          className="w-full px-3 py-2 bg-anthro-surface border border-anthro-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted"
        />
      </div>

      {/* Content */}
      <div>
        <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
          Content
        </label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Skill instructions (Markdown supported)"
          rows={10}
          className="w-full px-3 py-2 bg-anthro-surface border border-anthro-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted font-mono resize-y"
          required
        />
      </div>

      {/* Scope */}
      <div>
        <label className="block text-sm font-medium text-anthro-text-heading mb-2">
          Scope
        </label>
        <div className="flex flex-col gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="scope"
              value="project"
              checked={scope === 'project'}
              onChange={() => setScope('project')}
              className="accent-anthro-accent w-4 h-4"
            />
            <div className="flex items-baseline gap-2">
              <span className="text-sm text-anthro-text-body font-medium">Project</span>
              <span className="text-xs text-anthro-text-muted font-mono bg-anthro-bg px-1.5 py-0.5 rounded">./.claude/skills/</span>
            </div>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="scope"
              value="global"
              checked={scope === 'global'}
              onChange={() => setScope('global')}
              className="accent-anthro-accent w-4 h-4"
            />
            <div className="flex items-baseline gap-2">
              <span className="text-sm text-anthro-text-body font-medium">Global</span>
              <span className="text-xs text-anthro-text-muted font-mono bg-anthro-bg px-1.5 py-0.5 rounded">~/.claude/skills/</span>
            </div>
          </label>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-anthro-border">
        <Button variant="secondary" size="md" type="button" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="primary" size="md" type="submit" disabled={isSubmitDisabled}>
          Create Skill
        </Button>
      </div>
    </form>
  );
}
