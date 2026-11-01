# Starting the app

One launch script in the project folder brings RAG Studio up from nothing: it makes sure the container engine is running, starts every service, waits until they answer, starts the folder dialog helper, and opens the page in the browser.

## What the user can do

- **Run the launch script** from a terminal or from the file manager's right-click "Run with PowerShell" entry. Either works; on the older Windows shell the script hands itself to the newer one. If the newer shell is not installed, the script says how to install it and waits for Enter instead of closing.
- **Answer two short menus,** each of which picks its default after 5 seconds. Up/Down choose, Enter confirms, and a countdown shows the time left.
  1. **Build or no build:** start from the existing container images (the default and fast), or rebuild them first to pick up code changes.
  2. **Browser:** Chrome (the default) or the system's default browser.
- **Skip the menus with flags:** build, no build, Chrome or default browser. Both `--flag` and `-Flag` spellings are accepted, and contradictory flags are refused.

## The start, step by step

1. **Choices:** the menus run, unless flags already decided. They are also skipped when there is no keyboard (a scripted run), and the browser menu when Chrome is not installed.
2. **Container engine:** if Docker Desktop is not running, the script starts it and waits up to four minutes for it to answer. It finds Docker Desktop in the folder its installer recorded, so a custom install location works. If Docker Desktop is not installed, the script stops and says so.
3. **Graphics card:** the script asks the NVIDIA driver whether a graphics processing unit (GPU) is present. With one, the services get access to it and the app offers GPU choices. Without one (no NVIDIA card, or no driver), the script warns and the app starts CPU-only: every model runs on the central processing unit (CPU), and GPU choices are not offered.
4. **Services:** every service of the stack starts. "No build" still builds any image that does not exist yet, so a first run works without choosing Build.
5. **Readiness:** the script waits for the application programming interface (API) to report healthy (up to three minutes), then for the page itself (up to two).
6. **Folder dialog helper:** the small Windows-side program behind Browse… starts hidden. If one is already running it is reused. If the tool needed to run it is missing, the script warns that folders must be typed, and carries on.
7. **Browser:** the page opens in the chosen browser. Without Chrome, the default browser opens with a warning.
8. **Report:** the script prints where the app is running and that the Shut down button stops it.

## What the app does as it comes up

- **Jobs that were running when the app last stopped** are marked failed as "interrupted", so nothing appears stuck.
- **Databases and model servers whose containers no longer exist** are marked stopped. After a normal shutdown that is all of them, so the user starts what they need. Nothing loads onto the graphics card uninvited.
- **Partial downloads are deleted.** A download cut off by the last stop cannot be resumed, so its partial file is only wasted space. The terminal reports how much was freed.
- **Source folders are not required to exist.** Missing ones show as missing; startup never waits on them ([[Folders stay untouched]]).
- **Folder watching and the job queue start,** and the page begins polling for state once a second.

## Edge cases

- **Any step that times out stops the script with a message naming what did not become ready.** When it was started from the file manager, the window stays open so the error can be read.
- **A port already in use** by another program stops the start with the container engine's error. The app needs four fixed local ports: page, interface, folder dialog helper, and the database-based vector engine.
- **Running the script while the app is already up is harmless:** the services are already running, the helper is reused, and the page opens again.
- **A graphics card added or removed later** takes effect at the next start, because the check runs only then. A database whose embedder was set to the GPU cannot start on a CPU-only start; switching its embedder to the CPU fixes that.
- **The app keeps its data wherever its project folder is,** because the stack's name is fixed rather than derived from the folder.

## Related ideas

- [[Shutting down the app]], [[App components]], [[Kept and removed]]
