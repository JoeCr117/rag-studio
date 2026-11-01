# Local and private

Everything in RAG Studio runs on the user's computer, and their files, queries and answers never leave it. The only outside contact is downloading open models.

- **No online model services:** embedding, reranking and answering all run on local model servers, on the central processing unit (CPU) or graphics card.
- **No accounts:** only models that download without signing in are offered. Nothing in the app asks for a login.
- **Listens on this computer only:** the page, the application programming interface (API) and the folder dialog helper answer only local connections.
- **Other websites cannot drive it:** a page open in another browser tab could otherwise send requests to the local interface, such as shut down or download a model. Any request that changes something is refused unless it comes from RAG Studio's own page. The folder dialog helper applies the same rule.
- **Other websites cannot read it either:** a website can point its own address at this computer and then read local services as if they were its own. The interface and the folder dialog helper answer only requests addressed to this computer by name, and the vector engine with no such check is not reachable from outside the app at all.
- **Answers cannot reach out:** an answer can contain formatting and links, but never images or page code, so showing it never makes the browser fetch anything.
- **Downloads are visible and reversible:** the [[Model library]] shows what was fetched, from where, how large it is and where it sits, and deletes it on request.
- **Sized for one ordinary machine:** the model lists are chosen to fit one graphics card of about 12 gigabytes, with the [[GPU memory guard]] catching combinations that would not.

## Related ideas

- [[Folders stay untouched]], [[Hugging Face]]
