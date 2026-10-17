import io

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def make_file(text, filename):
    return (
        io.BytesIO(text.encode("utf-8")),
        filename
    )


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"SpecGuard" in response.data


def test_history_page(client):
    response = client.get("/history")

    assert response.status_code == 200
    assert b"Comparison history" in response.data


def test_compare_requires_files(client):
    response = client.post(
        "/compare",
        data={},
        content_type="multipart/form-data"
    )

    assert response.status_code == 400


def test_reject_non_txt_file(client):
    data = {
        "old_file": make_file(
            "Old requirement",
            "old.pdf"
        ),
        "new_file": make_file(
            "New requirement",
            "new.txt"
        )
    }

    response = client.post(
        "/compare",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert b"Only .txt files" in response.data


def test_reject_empty_file(client):
    data = {
        "old_file": make_file(
            "",
            "old.txt"
        ),
        "new_file": make_file(
            "Requirement",
            "new.txt"
        )
    }

    response = client.post(
        "/compare",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert b"empty" in response.data


def test_compare_success(client):
    old_text = """
Session timeout is 30 minutes
Maximum upload size is 10 MB
"""

    new_text = """
Session timeout is 60 minutes
Maximum upload size is 25 MB
"""

    data = {
        "old_file": make_file(
            old_text,
            "old.txt"
        ),
        "new_file": make_file(
            new_text,
            "new.txt"
        )
    }

    response = client.post(
        "/compare",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 200
    assert b"Specification changes" in response.data
    assert b"CHANGED" in response.data


def test_api_compare(client):
    data = {
        "old_file": make_file(
            "Session timeout is 30 minutes",
            "old.txt"
        ),
        "new_file": make_file(
            "Session timeout is 60 minutes",
            "new.txt"
        )
    }

    response = client.post(
        "/api/compare",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 200

    json_data = response.get_json()

    assert json_data["summary"]["changed"] == 1
    assert json_data["summary"]["added"] == 0
    assert json_data["summary"]["removed"] == 0

    assert (
        json_data["changes"][0]["status"]
        == "CHANGED"
    )


def test_missing_history_record(client):
    response = client.get(
        "/history/999999"
    )

    assert response.status_code == 404


def test_missing_report(client):
    response = client.get(
        "/report/999999"
    )

    assert response.status_code == 404