
import re


SECURITY_KEYWORDS = {
    "password",
    "authentication",
    "login",
    "session",
    "permission",
    "access",
    "authorization",
    "encryption",
    "token",
    "security",
    "credential",
    "mfa",
    "2fa"
}


def contains_security_keywords(text):
    """
    Detect security-related keywords as whole words.
    """
    if not text:
        return False

    words = set(
        re.findall(r"[a-z0-9]+", text.lower())
    )

    return bool(words & SECURITY_KEYWORDS)


def analyze_risk(result):
    """
    Assign a rule-based review priority.

    NONE:
        Requirement is unchanged.

    MEDIUM:
        Requirement was added or changed
        without a recognized security keyword.

    HIGH:
        Requirement was removed or a changed
        requirement contains security keywords.

    These labels are heuristic review priorities,
    not validated security risk assessments.
    """

    status = result.get("status")

    old_requirement = result.get("old") or ""
    new_requirement = result.get("new") or ""

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
        security_sensitive = (
            contains_security_keywords(old_requirement)
            or contains_security_keywords(new_requirement)
        )

        if security_sensitive:
            return {
                "level": "HIGH",
                "reason": (
                    "Security-sensitive requirement "
                    "was changed."
                )
            }

        return {
            "level": "MEDIUM",
            "reason": "Requirement was changed."
        }

    return {
        "level": "UNKNOWN",
        "reason": "Unsupported comparison status."
    }
