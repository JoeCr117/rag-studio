import { afterEach, describe, expect, it, vi } from "vitest";

import { FOLDER_PICKER_OFFLINE, FOLDER_PICKER_URL, pickFolder, stopFolderPicker } from "./folderPicker";

afterEach(() => vi.unstubAllGlobals());

describe("stopFolderPicker", () => {
  it("asks the helper to exit with the marker header", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({ ok: true })));
    vi.stubGlobal("fetch", fetchMock);
    await stopFolderPicker();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`${FOLDER_PICKER_URL}/shutdown`);
    expect(new Headers(init?.headers).get("X-RAG-Studio")).toBe("1");
  });

  it("does not fail shut down when the helper is not running", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(stopFolderPicker()).resolves.toBeUndefined();
  });
});

describe("pickFolder", () => {
  it("asks the helper with the marker header and returns the chosen path", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({ path: "W:\\Notes" })));
    vi.stubGlobal("fetch", fetchMock);
    await expect(pickFolder("W:\\")).resolves.toBe("W:\\Notes");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`${FOLDER_PICKER_URL}/pick-folder`);
    expect(new Headers(init?.headers).get("X-RAG-Studio")).toBe("1");
    expect(JSON.parse(String(init?.body))).toEqual({ start: "W:\\" });
  });

  it("returns null when the dialog is cancelled", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ path: null }))));
    await expect(pickFolder("")).resolves.toBeNull();
  });

  it("explains how to start the helper when it is not running", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(pickFolder("")).rejects.toThrow(FOLDER_PICKER_OFFLINE);
  });
});
