# Browsing contents

The Browse tab shows what is actually stored inside a database, document by document and chunk by chunk, so the user can see how their files were split and embedded.

## What the user can do

- **Pick a database,** then narrow its documents by source and by text in the file path.
- **Open a document** to see all of its chunks.
- **Expand a chunk** to see the exact text that was embedded and the start of its vector.

## How it behaves

- **The document list** shows each file's path, source and chunk count, and refreshes when the database's document count changes.
- **An opened document** shows its chunk count and when it was ingested.
- **Each chunk** shows:
  - its number;
  - its length in characters;
  - its vector's [[Dimensions]] and length ([[Vector norm]]);
  - its full text.
- **The expanded view** shows the chunk with its [[File header]], as it was sent to the embedder. It notes that a model's document prefix, if any, is added on top. Then it shows the first few numbers of the vector and how many dimensions there are in total.
- **Browsing works while the database is stopped,** because reading stored chunks needs no embedder.

## Related ideas

- [[Document]], [[Chunk]], [[Vectors]]
