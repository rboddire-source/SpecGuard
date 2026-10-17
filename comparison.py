from difflib import SequenceMatcher


SIMILARITY_THRESHOLD = 0.55


def similarity(text1, text2):
    """
    Return a similarity score between 0 and 1.
    """

    return SequenceMatcher(
        None,
        text1.lower().strip(),
        text2.lower().strip()
    ).ratio()


def compare_requirements(old_requirements, new_requirements):
    results = []

    # Keep track of new requirements that have already been paired.
    matched_new = set()

    # ---------------------------------------------------------
    # PASS 1: Find exact matches first
    # ---------------------------------------------------------

    matched_old = set()

    for old_index, old_requirement in enumerate(old_requirements):

        for new_index, new_requirement in enumerate(new_requirements):

            if new_index in matched_new:
                continue

            if old_requirement.strip() == new_requirement.strip():

                results.append({
                    "status": "UNCHANGED",
                    "old": old_requirement,
                    "new": new_requirement,
                    "similarity": 1.0
                })

                matched_old.add(old_index)
                matched_new.add(new_index)

                break

    # ---------------------------------------------------------
    # PASS 2: Match similar requirements
    # ---------------------------------------------------------

    for old_index, old_requirement in enumerate(old_requirements):

        if old_index in matched_old:
            continue

        best_score = 0
        best_new_index = None

        for new_index, new_requirement in enumerate(new_requirements):

            if new_index in matched_new:
                continue

            score = similarity(
                old_requirement,
                new_requirement
            )

            if score > best_score:
                best_score = score
                best_new_index = new_index

        if (
            best_new_index is not None
            and best_score >= SIMILARITY_THRESHOLD
        ):

            results.append({
                "status": "CHANGED",
                "old": old_requirement,
                "new": new_requirements[best_new_index],
                "similarity": round(best_score, 2)
            })

            matched_new.add(best_new_index)

        else:

            results.append({
                "status": "REMOVED",
                "old": old_requirement,
                "new": None,
                "similarity": 0
            })

    # ---------------------------------------------------------
    # PASS 3: Anything remaining in NEW is newly added
    # ---------------------------------------------------------

    for new_index, new_requirement in enumerate(new_requirements):

        if new_index not in matched_new:

            results.append({
                "status": "ADDED",
                "old": None,
                "new": new_requirement,
                "similarity": 0
            })

    return results