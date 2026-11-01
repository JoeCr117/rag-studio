"use client";

import * as HoverCard from "@radix-ui/react-hover-card";
import { useState, type ReactNode } from "react";

import { glossaryNote, obsidianLink, type GlossaryNote } from "@/lib/glossary";

interface Props {
  /** Name of a note in RAGStudioVault; its first paragraph is the explanation. */
  note: string;
  /** What this particular element means right now, shown above the note's general explanation. */
  detail?: string;
  /** Make the single child element (a pill, a span) the hover target instead of wrapping it in an underlined span. */
  asChild?: boolean;
  children: ReactNode;
}

/** A learning popup on hover or keyboard focus: the vault note's first paragraph and a link to the full note. */
export function Explained({ note, detail, asChild, children }: Props) {
  const [loaded, setLoaded] = useState<GlossaryNote | "missing" | null>(null);

  function loadOnOpen(open: boolean) {
    if (open && loaded === null) glossaryNote(note).then(setLoaded, () => setLoaded("missing"));
  }

  return (
    <HoverCard.Root openDelay={300} closeDelay={150} onOpenChange={loadOnOpen}>
      <HoverCard.Trigger asChild className={asChild ? "explained-target" : undefined}>
        {asChild ? (
          children
        ) : (
          // oxlint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- focusable so keyboard users can open the explanation
          <span className="explained" tabIndex={0}>{children}</span>
        )}
      </HoverCard.Trigger>
      <HoverCard.Portal>
        <HoverCard.Content className="explainer" side="top" sideOffset={6} collisionPadding={12}>
          <strong>{note}</strong>
          {detail && <p className="explainer-detail">{detail}</p>}
          <p>{loaded === null ? "Loading…" : loaded === "missing" ? "No vault note found for this item." : loaded.summary}</p>
          {loaded !== null && loaded !== "missing" && <a href={obsidianLink(loaded.path)}>Open the full note in Obsidian →</a>}
          <HoverCard.Arrow className="explainer-arrow" />
        </HoverCard.Content>
      </HoverCard.Portal>
    </HoverCard.Root>
  );
}
