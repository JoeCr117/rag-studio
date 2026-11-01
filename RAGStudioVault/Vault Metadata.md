# Vault Metadata

The rules of this vault: what belongs in it, how it is organized, and how to add to it or change it. This is the only note that describes the vault itself.

## What belongs in the vault

- **Purpose:** education. A note exists to teach a concept, a tool or a practice.
- **One area describes the app itself:** [[RagStudio]] documents RAG Studio's features, start, shutdown and design as behaviour, never as implementation: no file names, code, libraries or exact settings files. It should be enough to rebuild a similar app. Its notes link to the concept notes rather than re-explaining them.
- **No history of the vault:** what was tried, changed, renamed or removed is not recorded in notes.
- **No vault housekeeping in topic notes:** a topic note does not describe this vault's settings, rules or state. That goes here.
- **Two notes are about the vault:** [[Home]] says what the vault is for; this note says how it works.
- **Worked examples are welcome:** a note may use RAG Studio as its example, as long as the example teaches the topic.

## Structure

- **Shape:** Home → area → group → note. Home links only to areas, an area only to its groups, a group to its notes.
- **Hub notes:** every folder has a hub note with the same name as the folder. The hub lists what the folder holds, one line each.
- **One home per note:** a note lives in exactly one folder and is listed once, in that folder's hub.
- **Depth:** a topic may go deeper than three levels when it needs to. Each level follows the same folder-and-hub pattern.
- **Cross-links:** link freely between notes in different groups. Those are the crosses in the graph view.

## Names

- **Unique across the vault.** Links find a note by name, not by folder.
- **An area's name appears only inside that area.** No folder or note outside an area may contain the area's name, because path searches and graph colour groups match by text.
- **Plugin notes** are named after the plugin plus the word "plugin", so they cannot collide with a note on the underlying subject.

## Note format

1. The title, as a level-one heading identical to the file name.
2. A blank line.
3. One paragraph that defines the subject in a sentence or two.
4. Bullets and sections after that.

- **No properties block.** The title is always the first line.
- **Every acronym is spelled out** the first time it appears in a note.
- **Example files** (a `.base` or `.canvas`) sit beside the note that explains them and are embedded in it.

## Adding and changing

| Task | Steps |
| --- | --- |
| Add a note | Create it in the best-fitting folder; add one line for it to that folder's hub |
| Add a group | Needs three or more notes that share a purpose. Create the folder and its hub; add the hub to the area's hub |
| Add an area | Create the folder and its hub; add the hub to [[Home]] |
| Grow a note into a topic | Create a folder with the note's name, move the note inside (it becomes the hub), add the new notes and list them in it |
| Rename or move a note | Rename it in Obsidian so links update; fix its line in the old and new hubs |
| Remove a note | Delete it, remove its hub line, and remove or redirect links to it |
| Update a note | Change the note. Do not add a remark about what it used to say |

## RAG Studio depends on some notes

RAG Studio's hover explanations are read from this vault.

- A label with a dotted underline names a note. The API finds the note by name, in any folder, and the popup shows its first paragraph with a link that opens the note in Obsidian.
- So a note that RAG Studio refers to must keep its exact name, and its first paragraph must stand alone as the explanation: links in it show as plain text and formatting is dropped.
- This is also why notes have no properties block.
- The API reads the vault live, so an edited note shows in the popup on the next hover, without a rebuild.

## Repository

- **The vault lives in the RAG Studio project folder,** as `RAGStudioVault/`. Opening that folder in Obsidian opens the vault.
- **[[Home]] is the front page.** There is no separate `README.md`; how to open the vault is on Home.
- **Not committed:** `.obsidian/workspace.json`, the layout currently on screen, which changes whenever a tab moves. The vault's `.gitignore` keeps it out.

## Vault settings

- **Link format:** shortest path, so links carry the note name only.
- **Tags:** not used. Grouping is by folder and hub.
- **Templates and daily notes:** not used.
- **Backlinks:** shown at the bottom of every note.
- **Community plugins:** none.
- **Graph colour groups:** none.
- **Excluded files:** none.

## Checks

The checks live in RAG Studio's backend. `uv --directory backend run pytest tests/test_glossary_vault.py`, run from the RAG Studio folder, fails when:

- two notes share a name;
- a link points at a note that does not exist;
- a note is missing from its folder's hub;
- a note does not open with its title and a summary paragraph;
- a path outside an area contains that area's name;
- RAG Studio's interface refers to a note that does not exist.
