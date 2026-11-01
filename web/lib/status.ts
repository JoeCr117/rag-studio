import type { AssignmentStatus, Database, Source } from "./api";

export const STATUS_LABELS: Record<AssignmentStatus, string> = {
  synced: "Synced",
  changed: "Changed",
  never_synced: "Not synced",
  missing: "Folder missing",
  disconnected: "Disconnected",
};

export const STATUS_HINTS: Record<AssignmentStatus, string> = {
  synced: "The database matches the files on disk.",
  changed: "Files were added, edited or removed since the last sync.",
  never_synced: "Connected but nothing has been ingested yet.",
  missing: "The source folder is not on disk (moved, deleted or its drive disconnected). Stored chunks are kept.",
  disconnected: "Its chunks stay in the database until Sync all removes them.",
};

export function needsSync(status: AssignmentStatus): boolean {
  return status === "changed" || status === "never_synced";
}

export function unassignedSources(sources: Source[], database: Database): Source[] {
  const assigned = new Set(database.assignments.map((assignment) => assignment.source_id));
  return sources.filter((source) => !assigned.has(source.id));
}

export function unassignedDatabases(databases: Database[], source: Source): Database[] {
  const assigned = new Set(source.assignments.map((assignment) => assignment.database_id));
  return databases.filter((database) => !assigned.has(database.id));
}

/** Connected assignments of a source whose database is running, so a source-level Sync knows where to push. */
export function syncTargets(databases: Database[], source: Source): Database[] {
  return databases.filter((database) =>
    database.running && database.assignments.some((a) => a.source_id === source.id && a.connected),
  );
}
