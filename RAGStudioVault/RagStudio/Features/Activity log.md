# Activity log

RAG Studio shows what it is doing and what it has done: a list of jobs on the Manage tab, and a live terminal that slides up from the bottom of every tab.

## What the user can do

- **Read the job list:** recent jobs, each with its title, status (queued, running, done, failed) and its result or error message. The running job always appears, however long the queue, with its progress bar.
- **Open the terminal** from the header's Show terminal button, scroll back through history, clear it, and close it.
- **See whether the app is reachable:** the header shows API connected or API offline. The API is the application programming interface the page talks to.

## How it behaves

- **The terminal is live:**
  - lines stream in as the app works, from every part of it;
  - each line has its time, level and which part wrote it;
  - errors and warnings stand out by colour.
- **Opening it shows recent history,** not an empty screen, because lines are collected while the page is open and the server keeps a backlog.
- **It follows the newest line** unless the user has scrolled up to read.
- **Lines worth reading appear:**
  - every queued, started, finished and failed job;
  - every file added, updated or removed during a sync, with its chunk count;
  - sources that went missing;
  - each search's first words, mode and hit count;
  - model starts with their measured memory use.
- **Chunk text and answers are never logged.**
- **Old lines are trimmed** to the newest 5,000, so the log cannot grow without limit.
- **Errors also appear as a banner** at the top of the page, with a Dismiss button.
- **Progress is reported, not guessed:**
  - running jobs report how far along they are: files for syncs, bytes for downloads;
  - at most twice a second, so a fast loop does not flood the app;
  - the page draws a bar from each report on its once-a-second refresh.
  - A step that cannot count shows a moving bar and its title.

## Edge cases

- **The terminal reconnects by itself** if the stream drops, and shows "reconnecting" until it does.
- **Expected refusals** (such as syncing a stopped database) are logged as plain errors, without a crash report.

## Related ideas

- [[Jobs]], [[One job at a time]]
