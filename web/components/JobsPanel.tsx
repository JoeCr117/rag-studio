import type { Job } from "@/lib/api";

import { Explained } from "./Explained";
import { JobProgressBar } from "./JobActivity";

const SHOWN = 8;

export function JobsPanel({ jobs }: { jobs: Job[] }) {
  return (
    <section className="panel">
      <h2><Explained note="Jobs">Jobs</Explained></h2>
      <p className="hint">Run one at a time, oldest first. Full output is in the terminal.</p>
      {jobs.length === 0 && <p className="hint">Nothing has run yet.</p>}
      <ul className="jobs">
        {jobs.slice(0, SHOWN).map((job) => (
          <li key={job.id}>
            <span className={`pill job-${job.status}`}>{job.status}</span>
            <span className="job-title">{job.title}</span>
            {job.message && <span className={job.status === "failed" ? "error-text" : "hint"}>{job.message}</span>}
            {job.status === "running" && <div className="job-progress"><JobProgressBar job={job} /></div>}
          </li>
        ))}
      </ul>
    </section>
  );
}
