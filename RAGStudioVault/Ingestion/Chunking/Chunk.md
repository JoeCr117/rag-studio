# Chunk

One piece of a file: the unit that is embedded, stored, searched and handed to the generator.

- **Why files are cut up:** an embedding model reads only a limited number of [[Tokens]], and one vector for a whole long file would blur many topics together.
- **Where it splits:** Markdown files along their headings, other files along paragraphs and then lines, so a chunk rarely stops mid-sentence.
- **Sized in tokens:** see [[Chunk size]] and [[Chunk overlap]].
- **What is stored:** the chunk text, its [[File header]] and its vector. The Browse tab shows all three for any document.
- **In answers:** the chunks a search returns become the numbered [[Passages]] the generator reads.
