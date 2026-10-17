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

from comparison import compare_requirements


app = Flask(__name__)

# Maximum request size: 2 MB
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

ALLOWED_EXTENSIONS = {"txt"}


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def read_uploaded_file(file):
    if not file or file.filename == "":
        raise ValueError("Please select both specification files.")

    if not allowed_file(file.filename):
        raise ValueError("Only .txt files are supported.")

    try:
        content = file.read().decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Files must use UTF-8 text encoding.")

    if not content.strip():
        raise ValueError(
            f"{file.filename} is empty."
        )

    requirements = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    if not requirements:
        raise ValueError(
            f"{file.filename} contains no requirements."
        )

    return requirements


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

    summary = build_summary(results)

    return jsonify({
        "old_filename": old_file.filename,
        "new_filename": new_file.filename,
        "summary": summary,
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

    results = [
        {
            "status": change["status"],
            "old": change["old_requirement"],
            "new": change["new_requirement"],
            "similarity": change["similarity"]
        }
        for change in changes
    ]

    return render_template(
        "results.html",
        results=results,
        summary=summary,
        run_id=run_id,
        old_filename=comparison["old_filename"],
        new_filename=comparison["new_filename"]
    )


# ---------------------------------------------------------
# DOWNLOAD CSV REPORT
# ---------------------------------------------------------

@app.route("/report/<int:run_id>")
def download_report(run_id):
    comparison, changes = get_comparison(run_id)

    if comparison is None:
        return "Comparison not found.", 404

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "SpecGuard Comparison Report"
    ])

    writer.writerow([
        "Previous File",
        comparison["old_filename"]
    ])

    writer.writerow([
        "Current File",
        comparison["new_filename"]
    ])

    writer.writerow([
        "Created",
        comparison["created_at"]
    ])

    writer.writerow([])

    writer.writerow([
        "Status",
        "Previous Requirement",
        "Current Requirement",
        "Similarity"
    ])

    for change in changes:
        writer.writerow([
            change["status"],
            change["old_requirement"] or "",
            change["new_requirement"] or "",
            change["similarity"]
        ])

    response = make_response(output.getvalue())

    response.headers["Content-Type"] = (
        "text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        f'attachment; filename="'
        f'specguard_comparison_{run_id}.csv"'
    )

    return response


# ---------------------------------------------------------
# FILE TOO LARGE
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
        debug=True,
        use_reloader=False
    )