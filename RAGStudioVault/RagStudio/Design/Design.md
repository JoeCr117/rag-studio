# Design

The principles every feature of RAG Studio follows, and the parts the app is made of. A rebuild that keeps these keeps the app's character.

- [[App components]] — the moving parts and what each one is responsible for
- [[Local and private]] — everything runs and stays on the user's computer
- [[Folders stay untouched]] — source folders are only ever read, and a missing one never breaks anything
- [[One job at a time]] — slow work is queued and run in order, never in parallel
- [[Least privilege]] — only one part may start or stop containers, and only through fixed actions
- [[Nothing hidden]] — every intermediate result is visible, because the app exists to teach
