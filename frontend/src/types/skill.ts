import type { Scope, OverrideInfo } from './common';

export interface Skill {
  name: string;
  description: string;
  content?: string;
  scope: Scope;
  active: boolean;
  overridden?: OverrideInfo;
  source?: string;
  path?: string;
}

export interface SkillResponse {
  name: string;
  description: string;
  content: string;
  scope: Scope;
  active: boolean;
  overridden?: Record<string, unknown> | null;
  source?: string;
  path?: string;
}

export interface CreateSkillRequest {
  name: string;
  content: string;
  description?: string;
  scope: Scope;
}

export interface UpdateSkillRequest {
  content?: string;
  description?: string;
  scope?: Scope;
}
