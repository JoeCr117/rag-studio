import type { Job, JobProgress } from "./api";

export type JobMatcher = (job: Job) => boolean;

/** What a card should show: its running job, else its queued job (oldest first, the order the queue runs them). */
export function jobActivity(jobs: Job[], matches: JobMatcher): { running?: Job; queued?: Job } {
  const running = jobs.find((job) => job.status === "running" && matches(job));
  const queued = jobs.filter((job) => job.status === "queued" && matches(job)).at(-1);
  return { running, queued: running ? undefined : queued };
}

function formatBytes(bytes: number): string {
  return bytes >= 1e9 ? `${(bytes / 1e9).toFixed(2)} GB` : `${Math.round(bytes / 1e6)} MB`;
}

function formatAmount(amount: number, unit: JobProgress["unit"]): string {
  return unit === "bytes" ? formatBytes(amount) : `${amount.toLocaleString()} files`;
}

/** Percent is null while the total is unknown, so the bar shows activity instead of a guess. */
export function progressSummary(progress: JobProgress): { percent: number | null; amount: string } {
  const { done, total, unit } = progress;
  if (!total) return { percent: null, amount: done ? formatAmount(done, unit) : "" };
  const percent = Math.min(100, Math.floor((done / total) * 100));
  const amount = unit === "bytes" ? `${formatBytes(done)} of ${formatBytes(total)}` : `${done.toLocaleString()} of ${formatAmount(total, unit)}`;
  return { percent, amount };
}
