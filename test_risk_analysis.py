from risk_analysis import analyze_risk


def test_unchanged_has_no_risk():
    result = {
        "status": "UNCHANGED"
    }

    risk = analyze_risk(result)

    assert risk["level"] == "NONE"


def test_security_change_has_high_risk():
    result = {
        "status": "CHANGED",
        "new": "Session timeout is 60 minutes"
    }

    risk = analyze_risk(result)

    assert risk["level"] == "HIGH"

def test_added_requirement_has_medium_risk():
    result = {
        "status": "ADDED"
    }

    risk = analyze_risk(result)

    assert risk["level"] == "MEDIUM"

def test_removed_requirement_has_high_risk():
    result = {
        "status": "REMOVED"
    }

    risk = analyze_risk(result)

    assert risk["level"] == "HIGH"

def test_normal_change_has_medium_risk():
    result = {
        "status": "CHANGED",
        "new": "The system shall support multiple languages."
    }

    risk = analyze_risk(result)

    assert risk["level"] == "MEDIUM"