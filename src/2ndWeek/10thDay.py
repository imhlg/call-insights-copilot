def best_faq(scores, threshold=0.5):
    """Return the name of the highest-scoring FAQ entry.

    Args:
        scores: Mapping of FAQ name to relevance score (float). An empty
            mapping returns ``None`` since there is no candidate.
        threshold: Minimum score a match must reach to be accepted; below it,
            the entry is treated as no good match and ``None`` is returned.

    Returns:
        The FAQ name with the highest score when that score reaches ``threshold``,
        otherwise ``None``.
    """
    best = max(scores, key=scores.get)
    # best = max(scores, key=lambda name: scores[name])
    if scores[best] < threshold:
        return None
    return best

# print(best_faq({"refunds": 0.998, "bill_credit": 0.974, "plan_change": 0.281}))
print(best_faq({"refunds": 0.31, "bill_credit": 0.22, "plan_change": 0.18}))


def answer(scores, faqs, threshold=0.5):
    """Match a customer question to the best FAQ and build an answer payload.

    Args:
        scores: Mapping of FAQ name to relevance score (float).
        faqs:    Mapping of FAQ name to the canonical answer text.
        threshold: Minimum score for a match to be used; otherwise the payload
            flags that no good FAQ match exists.

    Returns:
        A dict with ``answer`` and ``source`` (and ``score``) when a match is
        found, or ``{"answer": None, "source": None,
        "note": "no good match, send to a human"}`` when no score reaches
        ``threshold``.
    """
    name = best_faq(scores, threshold)
    if name is None:
        return {"answer": None, "source": None, "note": "no good match, send to a human"}
    return {"answer": faqs[name], "source": name, "score": scores[name]}

# print(answer({"refunds": 0.998, "bill_credit": 0.974, "plan_change": 0.281}, FAQS))
print(answer({"refunds": 0.31, "bill_credit": 0.22, "plan_change": 0.18}, FAQS))