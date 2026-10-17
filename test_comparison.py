from comparison import compare_requirements


def count_status(results, status):
    return sum(
        result["status"] == status
        for result in results
    )


def test_unchanged_requirement():
    old = ["Users can download reports"]
    new = ["Users can download reports"]

    results = compare_requirements(old, new)

    assert count_status(results, "UNCHANGED") == 1
    assert count_status(results, "CHANGED") == 0


def test_changed_requirement():
    old = ["Session timeout is 30 minutes"]
    new = ["Session timeout is 60 minutes"]

    results = compare_requirements(old, new)

    assert count_status(results, "CHANGED") == 1

    assert results[0]["old"] == \
        "Session timeout is 30 minutes"

    assert results[0]["new"] == \
        "Session timeout is 60 minutes"


def test_added_requirement():
    old = [
        "Users must log in"
    ]

    new = [
        "Users must log in",
        "Two-factor authentication is required"
    ]

    results = compare_requirements(old, new)

    assert count_status(results, "UNCHANGED") == 1
    assert count_status(results, "ADDED") == 1


def test_removed_requirement():
    old = [
        "Users must log in",
        "Two-factor authentication is required"
    ]

    new = [
        "Users must log in"
    ]

    results = compare_requirements(old, new)

    assert count_status(results, "UNCHANGED") == 1
    assert count_status(results, "REMOVED") == 1


def test_inserted_requirement_does_not_shift_matching():
    old = [
        "Users must log in with email and password",
        "Password must contain at least 8 characters",
        "Session timeout is 30 minutes",
        "Maximum upload size is 10 MB",
        "Users can download reports"
    ]

    new = [
        "Users must log in with email and password",
        "Two-factor authentication is required",
        "Password must contain at least 12 characters",
        "Session timeout is 60 minutes",
        "Maximum upload size is 25 MB",
        "Users can download reports"
    ]

    results = compare_requirements(old, new)

    assert count_status(results, "CHANGED") == 3
    assert count_status(results, "ADDED") == 1
    assert count_status(results, "REMOVED") == 0
    assert count_status(results, "UNCHANGED") == 2