import { describe, expect, it } from "vitest";

import type { Job } from "./api";
import { jobActivity, progressSummary } from "./progress";

function job(id: number, status: Job["status"], database_id: number | null = 1): Job {
  return {
    id, kind: "sync_all", status, title: `job ${id}`, message: "", database_id, source_id: null, model_key: "",
    progress: null, created_at: "", finished_at: null,
  };
}

describe("jobActivity", () => {
  const forDatabase = (id: number) => (candidate: Job) => candidate.database_id === id;

  it("shows the running job and hides queued ones behind it", () => {
    const jobs = [job(3, "queued"), job(2, "running"), job(1, "done")];
    expect(jobActivity(jobs, forDatabase(1))).toEqual({ running: jobs[1], queued: undefined });
  });

  it("shows the oldest queued job when nothing of its own runs", () => {
    const jobs = [job(5, "queued"), job(4, "queued"), job(3, "running", 2)];
    expect(jobActivity(jobs, forDatabase(1))).toEqual({ running: undefined, queued: jobs[1] });
  });

  it("shows nothing when no job matches", () => {
    expect(jobActivity([job(1, "running", 2)], forDatabase(1))).toEqual({ running: undefined, queued: undefined });
  });
});

describe("progressSummary", () => {
  it("counts files with a percentage", () => {
    expect(progressSummary({ done: 12, total: 40, unit: "files", detail: "" })).toEqual({ percent: 30, amount: "12 of 40 files" });
  });

  it("shows downloads in megabytes, then gigabytes", () => {
    expect(progressSummary({ done: 250e6, total: 5.3e9, unit: "bytes", detail: "" })).toEqual({
      percent: 4, amount: "250 MB of 5.30 GB",
    });
  });

  it("has no percentage while the total is unknown", () => {
    expect(progressSummary({ done: 0, total: null, unit: "files", detail: "Rebuilding" })).toEqual({ percent: null, amount: "" });
  });
});
