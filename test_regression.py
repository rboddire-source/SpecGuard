
import pytest

from comparison import compare_requirements
from risk_analysis import analyze_risk


@pytest.mark.parametrize(
    "old_text,new_text,expected_status,expected_risk",
    [
        (
            "Users must enable MFA",
            "Users must not enable MFA",
            "CHANGED",
            "HIGH",
        ),
        (
            "Upload limit is 10 MB",
            "Upload limit is 25 MB",
            "CHANGED",
            "MEDIUM",
        ),
        (
            "Users can reset passwords",
            "Users can reset passwords",
            "UNCHANGED",
            "NONE",
        ),
        (
            "The system supports CSV export",
            "The system supports PDF export",
            "CHANGED",
            "MEDIUM",
        ),
    ],
)
def test_requirement_changes_and_risk(
    old_text, new_text, expected_status, expected_risk
):
    results = compare_requirements([old_text], [new_text])

    assert len(results) == 1
    assert results[0]["status"] == expected_status
    assert analyze_risk(results[0])["level"] == expected_risk


def test_security_keyword_in_old_requirement():
    result = {
        "status": "CHANGED",
        "old": "Password expires after 30 days",
        "new": "Credentials expire after 60 days",
    }

    assert analyze_risk(result)["level"] == "HIGH"


def test_security_keyword_does_not_match_inside_other_word():
    result = {
        "status": "CHANGED",
        "old": "Accessory color is blue",
        "new": "Accessory color is red",
    }

    assert analyze_risk(result)["level"] == "MEDIUM"


def test_duplicate_requirements_are_preserved():
    results = compare_requirements(
        ["Users can export reports", "Users can export reports"],
        ["Users can export reports"],
    )

    statuses = [result["status"] for result in results]

    assert statuses.count("UNCHANGED") == 1
    assert statuses.count("REMOVED") == 1


def test_added_and_removed_requirements():
    added = compare_requirements([], ["New reporting feature"])
    removed = compare_requirements(["Old reporting feature"], [])

    assert added[0]["status"] == "ADDED"
    assert removed[0]["status"] == "REMOVED"
    assert analyze_risk(added[0])["level"] == "MEDIUM"
    assert analyze_risk(removed[0])["level"] == "HIGH"
