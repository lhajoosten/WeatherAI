// Central feature flag parsing
// Reads build-time Vite envs (import.meta.env.*)
export interface Flags {
  ragEnabled: boolean;
}

function toBool(v: unknown): boolean {
  return v === '1' || v === 'true';
}

// Single generic flag env as per decision: VITE_FEATURE_FLAG
// Interpreted specifically at this stage as 'enable RAG feature surfaces'
export const flags: Flags = {
  ragEnabled: toBool(import.meta.env.VITE_FEATURE_FLAG),
};

export function isRagEnabled(): boolean {
  return flags.ragEnabled;
}