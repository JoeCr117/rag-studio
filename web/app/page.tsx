"use client";

import { useEffect, useState } from "react";

import { AskPanel } from "@/components/AskPanel";
import { BrowsePanel } from "@/components/BrowsePanel";
import { DatabasesPanel } from "@/components/DatabasesPanel";
import { JobsPanel } from "@/components/JobsPanel";
import { ModelsPanel } from "@/components/ModelsPanel";
import { SearchPanel } from "@/components/SearchPanel";
import { SourcesPanel } from "@/components/SourcesPanel";
import { StudioHeader } from "@/components/StudioHeader";
import { TerminalDrawer } from "@/components/TerminalDrawer";
import type { StudioState } from "@/lib/api";
import { pickDatabase } from "@/lib/explore";
import { useStudioState, type Act, type StartGpu } from "@/lib/useStudioState";

const TABS = ["Manage", "Search", "Ask", "Browse", "Models"] as const;
type Tab = (typeof TABS)[number];

export default function StudioPage() {
  const { state, error, offline, act, startGpu, vramPrompt, confirmVram, dismissVram, clearError, shutdownPhase, shutDown } =
    useStudioState();
  const [terminalOpen, setTerminalOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("Manage");
  const [databaseId, setDatabaseId] = useState<number | null>(null);

  if (shutdownPhase) {
    return <ShutdownScreen phase={shutdownPhase} />;
  }

  return (
    <div className={terminalOpen ? "studio terminal-open" : "studio"}>
      <StudioHeader
        state={state}
        offline={offline}
        terminalOpen={terminalOpen}
        onToggleTerminal={() => setTerminalOpen((open) => !open)}
        onShutDown={shutDown}
      />
      <div className="tabs" role="tablist">
        {TABS.map((name) => (
          <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? "tab active" : "tab"} onClick={() => setTab(name)}>
            {name}
          </button>
        ))}
      </div>
      {vramPrompt && (
        <div className="banner banner-warn" role="alert">
          <span>{vramPrompt.message}</span>
          <span className="row">
            <button className="button button-warn" onClick={confirmVram}>Start anyway</button>
            <button className="link" onClick={dismissVram}>Cancel</button>
          </span>
        </div>
      )}
      {error && (
        <div className="banner banner-error" role="alert">
          <span>{error}</span>
          <button className="link" onClick={clearError}>Dismiss</button>
        </div>
      )}
      {state ? (
        <TabContent tab={tab} state={state} act={act} startGpu={startGpu} databaseId={databaseId} onSelectDatabase={setDatabaseId} />
      ) : (
        <main className="empty">{offline ? "Waiting for the API at localhost:8000…" : "Loading…"}</main>
      )}
      <TerminalDrawer open={terminalOpen} onClose={() => setTerminalOpen(false)} />
    </div>
  );
}

function ShutdownScreen({ phase }: { phase: "stopping" | "stopped" }) {
  useEffect(() => {
    // Browsers only let a script close a tab that a script opened; otherwise this does nothing and the message stays.
    if (phase === "stopped") window.close();
  }, [phase]);
  return (
    <main className="empty shutdown">
      <h1>{phase === "stopping" ? "Shutting down RAG Studio…" : "RAG Studio has stopped"}</h1>
      <p>
        {phase === "stopping"
          ? "Removing the embedder, generator and reranker containers, then stopping the stack."
          : "Every container is stopped; databases, models and settings are kept in their Docker volumes. You can close this tab."}
      </p>
      {phase === "stopped" && <p className="hint">Start again with <code>start.ps1</code> in the RAG Studio folder.</p>}
    </main>
  );
}

interface TabContentProps {
  tab: Tab;
  state: StudioState;
  act: Act;
  startGpu: StartGpu;
  databaseId: number | null;
  onSelectDatabase: (id: number) => void;
}

function TabContent({ tab, state, act, startGpu, databaseId, onSelectDatabase }: TabContentProps) {
  if (tab === "Manage") {
    return (
      <main className="columns">
        <SourcesPanel state={state} act={act} />
        <div className="stack">
          <DatabasesPanel state={state} act={act} startGpu={startGpu} />
          <JobsPanel jobs={state.jobs} />
        </div>
      </main>
    );
  }
  if (tab === "Models") {
    return <main className="single"><ModelsPanel state={state} act={act} /></main>;
  }
  const selected = pickDatabase(state.databases, databaseId);
  if (!selected) {
    return <main className="empty">Create a database on the Manage tab first.</main>;
  }
  const shared = { selected, onSelect: onSelectDatabase };
  return (
    <main className="single">
      {tab === "Search" && <SearchPanel databases={state.databases} servers={state.servers} {...shared} />}
      {tab === "Ask" && <AskPanel state={state} act={act} startGpu={startGpu} {...shared} />}
      {tab === "Browse" && <BrowsePanel key={selected.id} databases={state.databases} {...shared} />}
    </main>
  );
}
