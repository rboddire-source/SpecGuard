from difflib import SequenceMatcher, ndiff


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


def get_change_details(old_text, new_text):
    """
    Identify the words or values that changed between
    two versions of a requirement.
    """

    old_words = old_text.split()
    new_words = new_text.split()

    differences = ndiff(old_words, new_words)

    removed = []
    added = []

    for item in differences:
        if item.startswith("- "):
            removed.append(item[2:])

        elif item.startswith("+ "):
            added.append(item[2:])

    return {
        "removed": removed,
        "added": added
    }


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
                    "similarity": 1.0,
                    "changes": {
                        "removed": [],
                        "added": []
                    }
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

            new_requirement = new_requirements[best_new_index]

            results.append({
                "status": "CHANGED",
                "old": old_requirement,
                "new": new_requirement,
                "similarity": round(best_score, 2),
                "changes": get_change_details(
                    old_requirement,
                    new_requirement
                )
            })

            matched_new.add(best_new_index)

        else:

            results.append({
                "status": "REMOVED",
                "old": old_requirement,
                "new": None,
                "similarity": 0,
                "changes": {
                    "removed": [],
                    "added": []
                }
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
                "similarity": 0,
                "changes": {
                    "removed": [],
                    "added": []
                }
            })

    return results