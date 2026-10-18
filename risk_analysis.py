SECURITY_KEYWORDS = {
    "password",
    "authentication",
    "login",
    "session",
    "permission",
    "access"
}


def analyze_risk(result):
    """
    Assign a rule-based risk level to a requirement comparison result.

    Levels:
        NONE   - unchanged requirement
        MEDIUM - added or non-security changed requirement
        HIGH   - removed or security-sensitive changed requirement
    """

    status = result.get("status")

    if status == "UNCHANGED":
        return {
            "level": "NONE",
            "reason": "Requirement did not change."
        }

    if status == "ADDED":
        return {
            "level": "MEDIUM",
            "reason": "A new requirement was added."
        }

    if status == "REMOVED":
        return {
            "level": "HIGH",
            "reason": "An existing requirement was removed."
        }

    if status == "CHANGED":
        new_requirement = (result.get("new") or "").lower()

        if any(
            keyword in new_requirement
            for keyword in SECURITY_KEYWORDS
        ):
            return {
                "level": "HIGH",
                "reason": "Security-sensitive requirement was changed."
            }

        return {
            "level": "MEDIUM",
            "reason": "Requirement was changed."
        }

    return {
        "level": "UNKNOWN",
        "reason": "Unsupported comparison status."
    }