
from difflib import SequenceMatcher, ndiff
import re


SIMILARITY_THRESHOLD = 0.65


def normalize_text(text):
    """Normalize whitespace and capitalization."""
    return " ".join(text.lower().split())


def extract_requirement_id(text):
    """Extract a requirement ID such as REQ-101."""
    match = re.match(
        r"^\s*(REQ-\d+)\s*:",
        text,
        re.IGNORECASE
    )
    return match.group(1).upper() if match else None


def similarity(text1, text2):
    """Return character similarity between 0 and 1."""
    return SequenceMatcher(
        None,
        normalize_text(text1),
        normalize_text(text2),
        autojunk=False
    ).ratio()


def get_change_details(old_text, new_text):
    """Identify words removed and added."""
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


def extract_numbers(text):
    """Extract numeric values, including decimals."""
    return re.findall(r"\d+(?:\.\d+)?", text)


def important_words(text):
    """Extract meaningful words for comparison."""
    stopwords = {
        "the", "a", "an", "is", "are", "be",
        "to", "of", "in", "on", "for", "and",
        "or", "with", "by", "from", "that"
    }

    words = re.findall(r"[a-zA-Z]+", text.lower())

    return {
        word for word in words
        if word not in stopwords
    }


def word_overlap(text1, text2):
    """Calculate meaningful-word overlap."""
    words1 = important_words(text1)
    words2 = important_words(text2)

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union


def combined_similarity(text1, text2):
    """Combine character and word similarity."""
    character_score = similarity(text1, text2)
    overlap_score = word_overlap(text1, text2)

    return (
        0.7 * character_score
        + 0.3 * overlap_score
    )


def compare_requirements(old_requirements, new_requirements):
    """
    Compare two requirement lists.

    Returns statuses:
    UNCHANGED, CHANGED, REMOVED, ADDED.

    Matching priority:
    1. Unique requirement IDs
    2. Identical normalized text
    3. Similarity-based matching
    4. Remaining removals and additions
    """

    results = []

    matched_old = set()
    matched_new = set()

    # -----------------------------------------
    # PASS 0: Match unique requirement IDs
    # -----------------------------------------

    old_ids = {}
    new_ids = {}

    for i, text in enumerate(old_requirements):
        req_id = extract_requirement_id(text)
        if req_id:
            old_ids.setdefault(req_id, []).append(i)

    for i, text in enumerate(new_requirements):
        req_id = extract_requirement_id(text)
        if req_id:
            new_ids.setdefault(req_id, []).append(i)

    for req_id in old_ids.keys() & new_ids.keys():

        # Skip ambiguous duplicate IDs.
        if len(old_ids[req_id]) != 1:
            continue

        if len(new_ids[req_id]) != 1:
            continue

        old_index = old_ids[req_id][0]
        new_index = new_ids[req_id][0]

        old_text = old_requirements[old_index]
        new_text = new_requirements[new_index]

        unchanged = (
            normalize_text(old_text)
            == normalize_text(new_text)
        )

        results.append({
            "status": "UNCHANGED" if unchanged else "CHANGED",
            "old": old_text,
            "new": new_text,
            "similarity": (
                1.0 if unchanged
                else round(combined_similarity(old_text, new_text), 2)
            ),
            "changes": (
                {"removed": [], "added": []}
                if unchanged
                else get_change_details(old_text, new_text)
            )
        })

        matched_old.add(old_index)
        matched_new.add(new_index)

    # -----------------------------------------
    # PASS 1: Match identical requirements
    # -----------------------------------------

    new_lookup = {}

    for new_index, new_text in enumerate(new_requirements):

        if new_index in matched_new:
            continue

        key = normalize_text(new_text)
        new_lookup.setdefault(key, []).append(new_index)

    for old_index, old_text in enumerate(old_requirements):

        if old_index in matched_old:
            continue

        key = normalize_text(old_text)

        if key not in new_lookup:
            continue

        while new_lookup[key]:
            new_index = new_lookup[key].pop(0)

            if new_index in matched_new:
                continue

            new_text = new_requirements[new_index]

            results.append({
                "status": "UNCHANGED",
                "old": old_text,
                "new": new_text,
                "similarity": 1.0,
                "changes": {
                    "removed": [],
                    "added": []
                }
            })

            matched_old.add(old_index)
            matched_new.add(new_index)
            break

    # -----------------------------------------
    # PASS 2: Match similar requirements
    # -----------------------------------------

    candidates = []

    for old_index, old_text in enumerate(old_requirements):

        if old_index in matched_old:
            continue

        for new_index, new_text in enumerate(new_requirements):

            if new_index in matched_new:
                continue

            old_id = extract_requirement_id(old_text)
            new_id = extract_requirement_id(new_text)

            # Never match two different explicit IDs.
            if old_id and new_id and old_id != new_id:
                continue

            # Don't match an ID-bearing requirement
            # against an ID-less requirement.
            if bool(old_id) != bool(new_id):
                continue

            score = combined_similarity(old_text, new_text)

            if score >= SIMILARITY_THRESHOLD:
                candidates.append(
                    (score, old_index, new_index)
                )

    # Highest similarity first.
    candidates.sort(reverse=True)

    for score, old_index, new_index in candidates:

        if old_index in matched_old:
            continue

        if new_index in matched_new:
            continue

        old_text = old_requirements[old_index]
        new_text = new_requirements[new_index]

        results.append({
            "status": "CHANGED",
            "old": old_text,
            "new": new_text,
            "similarity": round(score, 2),
            "changes": get_change_details(
                old_text,
                new_text
            )
        })

        matched_old.add(old_index)
        matched_new.add(new_index)

    # -----------------------------------------
    # PASS 3: Identify removed requirements
    # -----------------------------------------

    for old_index, old_text in enumerate(old_requirements):

        if old_index not in matched_old:
            results.append({
                "status": "REMOVED",
                "old": old_text,
                "new": None,
                "similarity": 0,
                "changes": {
                    "removed": [],
                    "added": []
                }
            })

    # -----------------------------------------
    # PASS 4: Identify added requirements
    # -----------------------------------------

    for new_index, new_text in enumerate(new_requirements):

        if new_index not in matched_new:
            results.append({
                "status": "ADDED",
                "old": None,
                "new": new_text,
                "similarity": 0,
                "changes": {
                    "removed": [],
                    "added": []
                }
            })

    return results
