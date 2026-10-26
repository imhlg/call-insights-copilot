import math

refund_faq  = [0.9, 0.1]   # "money back" area
credit_faq  = [0.7, 0.3]   # also money, but a bill credit
plan_faq    = [0.1, 0.9]   # "change my plan" area

question = [0.85, 0.15]    # "I want my money back"

def cosine(a, b):
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector (sequence of numbers).
        b: Second vector (sequence of numbers).

    Returns:
        Cosine similarity as a float in [-1, 1]. 1 means identical direction,
        0 means orthogonal, -1 means opposite direction.
    """
    dot = sum(x * y for x, y in zip(a, b))
    # print(dot)
    len_a = math.sqrt(sum(x * x for x in a))
    len_b = math.sqrt(sum(y * y for y in b))
    # print("")
    return dot / (len_a * len_b)

print("refund:", round(cosine([1,0],[5,0]) , 3))

print("refund:", round(cosine(question, refund_faq), 3))
print("credit:", round(cosine(question, credit_faq), 3))
print("plan:  ", round(cosine(question, plan_faq), 3))