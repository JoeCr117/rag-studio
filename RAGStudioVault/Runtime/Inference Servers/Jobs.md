# Jobs

Longer tasks, such as creating, starting, syncing or deleting a database and downloading a model, queued and run one at a time by the worker.

- **One at a time:** two jobs never compete for the GPU (graphics processing unit) or the same database.
- **Statuses:** queued, running, done or failed, with a short message.
- **Progress:** a running sync counts files and a download counts bytes, shown as a bar on the job and on the card of what it works on. A step that cannot tell how far along it is shows a moving bar instead of a percentage. A waiting job says it is waiting in the queue.
- **Full output:** Show terminal at the top of the page.
- **Interrupted:** a job running when the worker stops is marked failed; run it again.
