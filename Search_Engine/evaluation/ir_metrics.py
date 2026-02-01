def precision(tp, fp):
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def recall(tp, fn):
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def f1_score(p, r):
    if p + r == 0:
        return 0.0
    return 2 * (p * r) / (p + r)


def average_precision(retrieved_ids, relevant_ids):
    """
    retrieved_ids: ranked list of doc_ids
    relevant_ids: set or list of relevant doc_ids
    """
    score = 0.0
    hits = 0

    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            hits += 1
            score += hits / i

    if not relevant_ids:
        return 0.0

    return score / len(relevant_ids)


def mean_average_precision(ap_list):
    if not ap_list:
        return 0.0
    return sum(ap_list) / len(ap_list)
