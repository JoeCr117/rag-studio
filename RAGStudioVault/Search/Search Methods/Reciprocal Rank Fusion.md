# Reciprocal Rank Fusion

A way to merge ranked lists using only each item's position: an item scores 1 divided by (60 + its rank) in each list, and the scores are added.

- **Also called:** RRF.
- **Why positions:** cosine similarities and keyword scores are on different scales and cannot be added. Ranks can.
- **Effect:** a chunk found by both searches beats one that tops only a single list.
- **Score range:** at most about 0.033, for first place in both lists (1/61 + 1/61). The order matters, not the absolute value.
- **The 60:** a damping constant from the original paper that stops the top rank from dominating. Both engines here use 60, so their scores compare.
- **Used by:** [[Hybrid search]].
