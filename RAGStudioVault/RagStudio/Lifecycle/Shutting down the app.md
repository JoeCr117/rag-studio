# Shutting down the app

The Shut down button in RAG Studio's header stops everything the app started: its model servers, its own services and the folder dialog helper. The user's data is kept for the next start.

## What the user can do

- **Press Shut down, then Confirm shut down,** or Cancel. The button is disabled when the app is not reachable. Its hover text warns when a job is running: a running download will be lost and start again from the beginning, and any other running job will be interrupted.

## The shutdown, step by step

1. **Queued jobs are cancelled** and marked "Cancelled: RAG Studio shut down". A running job is interrupted by the stop and marked as interrupted on the next start.
2. **Everything is marked stopped:** every database and model server, so the next start begins clean.
3. **The containers the app started itself are removed:** embedders, generator and reranker. Their graphics memory is freed at once.
4. **The stack is stopped from outside itself.** A short-lived helper container, which is not part of the stack, waits two seconds and then stops every service. It has to be outside the stack because the service handling the request is one of those being stopped. The delay lets the button's request finish first.
5. **The page changes to a shutdown screen:** "Shutting down RAG Studio…" with what is being removed. Then, once the app stops answering, "RAG Studio has stopped", saying that data and models are kept and that the launch script starts it again. The page tries to close its own tab, which browsers allow only for tabs a script opened.
6. **The folder dialog helper is told to exit** straight after the shutdown is accepted, and exits within moments.

## What is kept

- **All data volumes:** every database, all downloaded models, the app's settings, the source list, job history and logs. See [[Kept and removed]].
- **Container images,** so the next start is fast.

## Edge cases

- **Stopped some other way** (stopping the stack by hand, quitting Docker Desktop, a crash): the next start marks everything stopped that has no container. The folder dialog helper exits by itself once the app has been unreachable for a minute.
- **The helper was never started** (the app was started without the launch script): Shut down still works; there is just nothing extra to stop.
- **The shutdown request fails:** the error shows as a banner and the page stays usable. The services keep running, so Shut down can be pressed again.

## Related ideas

- [[Starting the app]], [[Least privilege]]
