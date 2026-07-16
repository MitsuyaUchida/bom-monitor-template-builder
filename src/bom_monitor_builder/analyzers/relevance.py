def calculate_relevance(target_name: str, candidate_name: str) -> tuple[int, str]:
    target = target_name.casefold().strip()
    candidate = candidate_name.casefold().strip()

    if not target or not candidate:
        return 0, "empty value"

    if target == candidate:
        return 100, "exact name match"

    if target in candidate or candidate in target:
        return 80, "partial name match"

    target_words = set(target.replace("-", " ").replace("_", " ").split())
    candidate_words = set(candidate.replace("-", " ").replace("_", " ").split())
    common = target_words & candidate_words

    if common:
        return 50, f"common keywords: {', '.join(sorted(common))}"

    return 0, "no relationship detected"
