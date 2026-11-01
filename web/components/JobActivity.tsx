import type { Job } from "@/lib/api";
import { jobActivity, progressSummary, type JobMatcher } from "@/lib/progress";

import { Explained } from "./Explained";

/** The bar's popup explains why it moves the way it does. */
function noteFor(job: Job): { note: string; detail: string } {
  if (job.progress?.unit === "bytes") {
    return { note: "Hugging Face", detail: "Downloaded once into the models volume; later starts reuse the file." };
  }
  if (job.progress?.unit === "files") {
    return { note: "Content hash", detail: "Unchanged files are only read and compared, so the bar speeds up over them." };
  }
  return { note: "Jobs", detail: "This step does not report how far along it is." };
}

/** A running job's progress bar: a percentage when the total is known, a moving bar otherwise. */
export function JobProgressBar({ job }: { job: Job }) {
  const summary = job.progress ? progressSummary(job.progress) : { percent: null, amount: "" };
  const { note, detail } = noteFor(job);
  return (
    <div className="progress">
      <div className="row progress-head">
        <Explained note={note} detail={detail}>{job.title}</Explained>
        <span className="spacer" />
        <span className="hint">{[summary.amount, summary.percent === null ? "" : `${summary.percent}%`].filter(Boolean).join(" · ")}</span>
      </div>
      {summary.percent === null ? (
        <progress aria-label={job.title} />
      ) : (
        <progress aria-label={job.title} value={summary.percent} max={100} />
      )}
      {job.progress?.detail && <code className="progress-detail" title={job.progress.detail}>{job.progress.detail}</code>}
    </div>
  );
}

/** What this card's thing is doing now: a progress bar while its job runs, a queue note while it waits. */
export function JobActivity({ jobs, matches }: { jobs: Job[]; matches: JobMatcher }) {
  const { running, queued } = jobActivity(jobs, matches);
  if (running) return <JobProgressBar job={running} />;
  if (queued) return <p className="hint">Waiting in the queue: {queued.title}</p>;
  return null;
}
