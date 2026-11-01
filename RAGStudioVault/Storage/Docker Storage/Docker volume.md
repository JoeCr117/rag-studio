# Docker volume

Storage that Docker manages separately from containers, so data survives when containers are removed, rebuilt or upgraded.

- **RAG Studio's volumes:** models (the downloaded [[GGUF]] files and tokenizers), meta-data (sources, databases and jobs), vector-data ([[pgvector]]) and qdrant-data ([[Qdrant]]).
- **Kept by:** Shut down, deleting containers and deleting images.
- **Deleted only by:** `docker compose down -v`, or removing the volume itself.
- **Seeing it:** Docker Desktop's Volumes tab, or the Windows path on the Models tab.
- **On disk:** inside Docker Desktop's virtual disk file, docker_data.vhdx.
