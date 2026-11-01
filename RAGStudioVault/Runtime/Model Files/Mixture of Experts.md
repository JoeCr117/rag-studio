# Mixture of Experts

A model design that splits each layer into many smaller expert networks and uses only a few of them per token, so a large model runs with the compute of a small one.

- **Also called:** MoE.
- **Total versus active:** Gemma 4 26B-A4B has 26 billion parameters in total but about 4 billion active per token; A4B means active 4 billion.
- **Memory still counts:** every expert must be loaded somewhere, even though few are used at once.
- **Experts in system RAM:** RAG Studio can keep some layers' experts in system RAM (random-access memory) when the model does not fit in [[VRAM]] (video random-access memory). It runs, but more slowly.
- **Speed:** LFM2.5 8B-A1B activates about 1 billion parameters per token, so it writes very fast.
