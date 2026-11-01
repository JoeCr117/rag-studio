# Least privilege

Each part of RAG Studio can do only what its job needs. The power to start and stop containers is the most dangerous one, so it is held by a single part and exposed only as a few fixed, checked actions.

- **One controller holds container control.** Every other part asks it for one of a fixed set of actions:
  - check that a folder is reachable;
  - start an embedder, the generator or the reranker;
  - stop one of the app's own containers;
  - list the app's containers;
  - shut down.
- **Every request is validated:** container names must be the app's own, model files must be plain file names inside the model volume, hardware and settings must come from the allowed lists. Nothing passes a free-form command through.
- **Read-only wherever possible:** source drives (worker only), the model volume (model servers), the note vault (the application programming interface, or API).
- **The folder dialog helper answers only RAG Studio's own page.** It checks where each request comes from, and refuses requests that lack the page's marker or that come through another site's address. Any other website cannot even make the dialog appear.
- **Everything listens on this computer only** ([[Local and private]]).

## Related ideas

- [[App components]], [[Shutting down the app]]
