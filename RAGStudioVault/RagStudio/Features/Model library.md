# Model library

The Models tab lists every model RAG Studio can use: what it is, whether it is downloaded, where its files are, and what uses it. The user can fetch a model ahead of time or delete it to free the disk space.

## What the user can do

- **See every model by role:** embedding models, generators and rerankers, each with its size and download status (downloaded, downloading, missing).
- **Download** a missing model before it is needed, so the first start is not slowed by a download.
- **Delete** a downloaded model after a confirmation that states the size being freed.
- **Find the files:** each model shows its path inside the containers and the path to paste into the Windows file manager. Each also links to the page it was downloaded from ([[Hugging Face]]).

## How it behaves

- **Models download themselves on first use.** Starting a database, generator or reranker whose model is missing downloads it first, so the Models tab is never a required step.
- **Every download shows a progress bar:**
  - it shows bytes received out of the file's size, the percentage, and the model's name;
  - it appears on the model's card, whatever started the download (the Download button or a start), and on the card of what is starting.
  - Until the download server reports the file's exact size, the catalog's size stands in.
  - A queued download says "Waiting in the queue".
- **Only models that download without an account** are offered.
- **All downloaded models live in one shared volume** ([[Docker volume]]), never inside a container image, so they survive rebuilds and are visible from Windows. A box at the top of the tab says so and gives the volume's paths.
- **Each model's name explains itself:** hovering it explains how to read a model's name (family, size, tuning, quantization) and shows the model's exact file name ([[Model file names]]).
- **Each card carries short facts** with explanations:
  - embedding models: [[Dimensions]] (and half precision above 2,000), [[Pooling]], [[Instruction prefix]]es;
  - generators: estimated graphics memory at an 8,192-token context ([[KV cache]]), and expert layers kept in system memory ([[Mixture of Experts]]);
  - rerankers: graphics memory on the graphics processing unit (GPU).
- **Embedding models also show their [[Tokenizer]]:** where it comes from and where it is cached. If it has not been fetched yet, the card says the first sync using the model will fetch it. Each embedding model also lists which databases use it.
- **Built-in keyword scorers** are listed in their own section, marked as living inside a container image. Each shows the image and the paths inside it, and says that nothing is downloaded for them ([[Docker image]]).

## Edge cases

- **A download interrupted** by a restart, shutdown or crash starts again from the beginning next time. Its partial file is deleted when the app next starts ([[Kept and removed]]).
- **Deleting is refused while the model is in use:** a running database or server uses it, or any job is queued or running.
- **Deleting removes everything downloaded for that model:**
  - the model file;
  - its download records;
  - for an embedding model, its cached tokenizer, including files shared inside the cache that no other tokenizer needs.

  The next start downloads it again.

## Related ideas

- [[Model Files]], [[GGUF]], [[Quantization]], [[Kept and removed]]
