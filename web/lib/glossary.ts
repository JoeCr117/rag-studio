import { request } from "./api";

/** The Obsidian vault (RAGStudioVault in this folder) that hover explanations come from; Obsidian knows it by folder name. */
export const GLOSSARY_VAULT = "RAGStudioVault";

export interface GlossaryNote {
  name: string;
  summary: string;
  /** Relative to the vault, without `.md`. */
  path: string;
}

const notes = new Map<string, Promise<GlossaryNote>>();

export function obsidianLink(path: string): string {
  return `obsidian://open?vault=${encodeURIComponent(GLOSSARY_VAULT)}&file=${encodeURIComponent(path)}`;
}

/** Fetched once per page load; a failed fetch is forgotten so the next hover retries. */
export function glossaryNote(name: string): Promise<GlossaryNote> {
  if (!notes.has(name)) {
    const pending = request<GlossaryNote>("GET", `/glossary/${encodeURIComponent(name)}`);
    pending.catch(() => notes.delete(name));
    notes.set(name, pending);
  }
  return notes.get(name)!;
}
