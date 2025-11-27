"""
Simple heuristic recommender for ranking restaurants from search results.
"""

def score_restaurant(r, party_size):
    # higher rating preferred; slight penalty for small capacity difference
    rating = r.get("rating", 3.0)
    capacity = r.get("capacity", 40)
    cap_penalty = max(0, (party_size - capacity) / max(1, capacity))
    # final score
    return rating - cap_penalty

def recommend(results, party_size=2, limit=3):
    scored = []
    for r in results:
        s = score_restaurant(r, party_size)
        rcopy = r.copy()
        rcopy["_score"] = s
        scored.append(rcopy)
    scored = sorted(scored, key=lambda x: x["_score"], reverse=True)
    return scored[:limit]
