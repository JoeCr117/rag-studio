"use client";

import { useEffect, useRef, useState } from "react";

import { API_URL } from "@/lib/api";

interface LogEvent {
  id: number;
  at: string;
  level: string;
  origin: string;
  message: string;
}

const KEEP = 2000;

/** Streams backend logs over Server-Sent Events while the page is open, so opening the drawer shows recent history. */
export function TerminalDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [lines, setLines] = useState<LogEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const body = useRef<HTMLDivElement>(null);
  const pinned = useRef(true);

  useEffect(() => {
    const source = new EventSource(`${API_URL}/api/logs/stream`);
    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    source.onmessage = (event) => {
      const line = { id: Number(event.lastEventId), ...JSON.parse(event.data) } as LogEvent;
      setLines((current) => (current.some((l) => l.id === line.id) ? current : [...current, line].slice(-KEEP)));
    };
    return () => source.close();
  }, []);

  useEffect(() => {
    if (open && pinned.current && body.current) body.current.scrollTop = body.current.scrollHeight;
    // oxlint-disable-next-line react/exhaustive-effect-dependencies -- scroll again whenever new lines arrive
  }, [lines, open]);

  return (
    <aside className={open ? "terminal open" : "terminal"} aria-hidden={!open}>
      <div className="terminal-bar">
        <strong>Terminal</strong>
        <span className={connected ? "pill pill-good" : "pill pill-bad"}>{connected ? "live" : "reconnecting"}</span>
        <span className="spacer" />
        <button className="link" onClick={() => setLines([])}>Clear</button>
        <button className="link" onClick={onClose}>Close</button>
      </div>
      <div
        className="terminal-body"
        ref={body}
        onScroll={(event) => {
          const element = event.currentTarget;
          pinned.current = element.scrollHeight - element.scrollTop - element.clientHeight < 24;
        }}
      >
        {lines.map((line) => (
          <div key={line.id} className={`log log-${line.level.toLowerCase()}`}>
            <span className="log-time">{new Date(line.at).toLocaleTimeString()}</span>
            <span className="log-origin">{line.origin}</span>
            <span className="log-message">{line.message}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}
