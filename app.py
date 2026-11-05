
import csv
import io
import os

from flask import (
    Flask,
    jsonify,
    make_response,
    render_template,
    request
)

from database import (
    create_database,
    save_comparison,
    get_history,
    get_comparison
)

from comparison import (
    compare_requirements,
    get_change_details
)

from risk_analysis import analyze_risk


app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

ALLOWED_EXTENSIONS = {"txt"}


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def allowed_file(filename):
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def read_uploaded_file(file):
    if not file or not file.filename:
        raise ValueError(
            "Please select both specification files."
        )

    if not allowed_file(file.filename):
        raise ValueError(
            "Only .txt files are supported."
        )

    try:
        content = file.read().decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            "Files must use UTF-8 text encoding."
        )

    if not content.strip():
        raise ValueError(
            "The uploaded file is empty."
        )

    requirements = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    if not requirements:
        raise ValueError(
            "The file contains no requirements."
        )

    return requirements


def add_risk_analysis(results):
    for result in results:
        result["risk"] = analyze_risk(result)

    return results


def build_summary(results):
    return {
        "changed": sum(
            r["status"] == "CHANGED"
            for r in results
        ),
        "added": sum(
            r["status"] == "ADDED"
            for r in results
        ),
        "removed": sum(
            r["status"] == "REMOVED"
            for r in results
        ),
        "unchanged": sum(
            r["status"] == "UNCHANGED"
            for r in results
        )
    }


def restore_results(changes):
    """
    Rebuild results from saved database records.

    Older comparisons may not have stored
    word-level change details.
    """

    results = []

    for change in changes:
        status = change["status"]
        old_text = change["old_requirement"]
        new_text = change["new_requirement"]

        details = change.get("changes")

        if not isinstance(details, dict):
            details = None

        if status == "CHANGED" and details is None:
            if old_text is not None and new_text is not None:
                details = get_change_details(
                    old_text,
                    new_text
                )

        if details is None:
            details = {
                "removed": [],
                "added": []
            }

        results.append({
            "status": status,
            "old": old_text,
            "new": new_text,
            "similarity": change["similarity"],
            "changes": details
        })

    return add_risk_analysis(results)


def safe_csv_value(value):
    """
    Prevent spreadsheet formula injection
    when exported CSV files are opened.
    """
    if value is None:
        return ""

    text = str(value)

    if text.lstrip().startswith(
        ("=", "+", "-", "@")
    ):
        return "'" + text

    return text


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------
# WEB COMPARISON
# ---------------------------------------------------------

@app.route("/compare", methods=["POST"])
def compare():
    old_file = request.files.get("old_file")
    new_file = request.files.get("new_file")

    try:
        old_requirements = read_uploaded_file(old_file)
        new_requirements = read_uploaded_file(new_file)
    except ValueError as error:
        return str(error), 400

    results = compare_requirements(
        old_requirements,
        new_requirements
    )

    results = add_risk_analysis(results)
    summary = build_summary(results)

    run_id = save_comparison(
        old_file.filename,
        new_file.filename,
        results,
        summary
    )

    return render_template(
        "results.html",
        results=results,
        summary=summary,
        run_id=run_id,
        old_filename=old_file.filename,
        new_filename=new_file.filename
    )


# ---------------------------------------------------------
# JSON API
# ---------------------------------------------------------

@app.route("/api/compare", methods=["POST"])
def api_compare():
    old_file = request.files.get("old_file")
    new_file = request.files.get("new_file")

    try:
        old_requirements = read_uploaded_file(old_file)
        new_requirements = read_uploaded_file(new_file)
    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    results = compare_requirements(
        old_requirements,
        new_requirements
    )

    results = add_risk_analysis(results)

    return jsonify({
        "old_filename": old_file.filename,
        "new_filename": new_file.filename,
        "summary": build_summary(results),
        "changes": results
    })


# ---------------------------------------------------------
# HISTORY
# ---------------------------------------------------------

@app.route("/history")
def history():
    rows = get_history()

    return render_template(
        "history.html",
        history=rows
    )


# ---------------------------------------------------------
# SAVED COMPARISON DETAILS
# ---------------------------------------------------------

@app.route("/history/<int:run_id>")
def comparison_details(run_id):
    comparison, changes = get_comparison(run_id)

    if comparison is None:
        return "Comparison not found.", 404

    summary = {
        "changed": comparison["changed_count"],
        "added": comparison["added_count"],
        "removed": comparison["removed_count"],
        "unchanged": comparison["unchanged_count"]
    }

    results = restore_results(changes)

    return render_template(
        "results.html",
        results=results,
        summary=summary,
        run_id=run_id,
        old_filename=comparison["old_filename"],
        new_filename=comparison["new_filename"]
    )


# ---------------------------------------------------------
# CSV REPORT
# ---------------------------------------------------------

@app.route("/report/<int:run_id>")
def download_report(run_id):
    comparison, changes = get_comparison(run_id)

    if comparison is None:
        return "Comparison not found.", 404

    results = restore_results(changes)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "SpecGuard Comparison Report"
    ])

    writer.writerow([
        "Previous File",
        safe_csv_value(comparison["old_filename"])
    ])

    writer.writerow([
        "Current File",
        safe_csv_value(comparison["new_filename"])
    ])

    writer.writerow([
        "Created",
        safe_csv_value(comparison["created_at"])
    ])

    writer.writerow([])

    writer.writerow([
        "Status",
        "Previous Requirement",
        "Current Requirement",
        "Similarity",
        "Risk Level",
        "Risk Reason"
    ])

    for result in results:
        risk = result["risk"]

        writer.writerow([
            safe_csv_value(result["status"]),
            safe_csv_value(result["old"]),
            safe_csv_value(result["new"]),
            result["similarity"],
            safe_csv_value(risk["level"]),
            safe_csv_value(risk["reason"])
        ])

    response = make_response(output.getvalue())

    response.headers["Content-Type"] = (
        "text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        f'attachment; filename="'
        f'specguard_comparison_{run_id}.csv"'
    )

    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


# ---------------------------------------------------------
# ERRORS
# ---------------------------------------------------------

@app.errorhandler(413)
def file_too_large(error):
    return (
        "Upload too large. Maximum request size is 2 MB.",
        413
    )


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":
    create_database()

    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
        use_reloader=False
    )
