/** The Windows-side helper (folder-picker/folder_picker.py, started by start.ps1) that opens Windows' own folder dialog. */
export const FOLDER_PICKER_URL = "http://127.0.0.1:8010";

export const FOLDER_PICKER_OFFLINE =
  "The Windows folder dialog is not running. Start RAG Studio with start.ps1, or type the path.";

const MARKER = { "X-RAG-Studio": "1" };

/** Part of Shut down. Never fails: the helper may not be running (RAG Studio started without start.ps1). */
export async function stopFolderPicker(): Promise<void> {
  try {
    await fetch(`${FOLDER_PICKER_URL}/shutdown`, { method: "POST", headers: MARKER });
  } catch {}
}

/** Opens the dialog at `start` (when it exists) and waits for it; null when the dialog is cancelled. */
export async function pickFolder(start: string): Promise<string | null> {
  let response: Response;
  try {
    response = await fetch(`${FOLDER_PICKER_URL}/pick-folder`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...MARKER },
      body: JSON.stringify({ start }),
    });
  } catch {
    throw new Error(FOLDER_PICKER_OFFLINE);
  }
  if (!response.ok) throw new Error(`The folder dialog helper refused the request (${response.status}).`);
  return (await response.json()).path;
}
