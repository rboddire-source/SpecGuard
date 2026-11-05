
from difflib import SequenceMatcher, ndiff
from collections import Counter
import re


SIMILARITY_THRESHOLD = 0.65


def normalize_text(text):
    """Normalize whitespace and capitalization."""
    return " ".join(text.lower().split())


def similarity(text1, text2):
    """Return similarity score between 0 and 1."""
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
    """Extract useful words for comparing requirements."""
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
    """Calculate overlap of meaningful words."""
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
    """

    results = []

    matched_old = set()
    matched_new = set()

    # PASS 1: Match identical requirements,
    # even if capitalization or spacing differs.
    new_lookup = {}

    for new_index, new_text in enumerate(new_requirements):
        key = normalize_text(new_text)
        new_lookup.setdefault(key, []).append(new_index)

    for old_index, old_text in enumerate(old_requirements):
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

    # PASS 2: Find candidate changed requirements.
    candidates = []

    for old_index, old_text in enumerate(old_requirements):
        if old_index in matched_old:
            continue

        for new_index, new_text in enumerate(new_requirements):
            if new_index in matched_new:
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

    # PASS 3: Identify removed requirements.
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

    # PASS 4: Identify added requirements.
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
