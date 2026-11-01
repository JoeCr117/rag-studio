# Nothing hidden

RAG Studio exists to teach how retrieval-augmented generation (RAG) works, so it shows every intermediate result rather than only the final one. A user should be able to see why an answer came out the way it did.

- **Scores with their meaning:** each result shows its fusion score, raw similarity, rerank score and its rank in each list, with a legend in plain words ([[Finding passages]]).
- **Timings for every step:** embedding the query, searching, reranking, reading the prompt and writing the answer, plus tokens per second.
- **The stored data itself:** chunk text, the exact text that was embedded, vector length and the first vector values ([[Browsing contents]]).
- **Where things live:** model files, tokenizers and built-in scorers, each with its paths inside the containers and on Windows ([[Model library]]).
- **Estimates next to measurements:** expected and measured graphics memory for every start ([[GPU memory guard]]).
- **Progress, not silence:** slow work shows how far along it is and what it is working on, and waiting work says it is queued.
- **Reasons, not dead buttons:** a disabled control says why, and a warning says what to do next.
- **A concept on screen is a door into this vault** ([[Learning popups]]).

## Related ideas

- [[Activity log]], [[RagStudio]]
