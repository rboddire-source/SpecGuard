# SpecGuard

**Requirement Change Intelligence for Software Specifications**

SpecGuard is a lightweight software engineering tool that compares two versions of a requirements specification and identifies meaningful changes between them.

Instead of manually reviewing requirement documents line by line, SpecGuard classifies requirements as **Changed, Added, Removed, or Unchanged**, identifies the exact words or values that changed, and assigns an explainable rule-based review priority.

## Live Demo

Try SpecGuard directly in your browser:

**https://rboddire-source.github.io/SpecGuard/**

> The live demo is a browser-based implementation designed for GitHub Pages.  
> The repository also contains the full Python/Flask application with SQLite persistence, REST API support, CSV reporting, and automated tests.

---

## Why SpecGuard?

Software requirements change throughout development.

A requirement such as:

```text
Session timeout is 30 minutes
```

may later become:

```text
Session timeout is 60 minutes
```

A simple text comparison can show that the sentences differ, but developers and reviewers often need more useful information:

- What exactly changed?
- Was a requirement added or removed?
- Which changes deserve closer review?
- Can previous comparisons be revisited?
- Can the results be exported or consumed through an API?

SpecGuard was built to explore these problems in a small, understandable software engineering system.

---

## Features

### Requirement Comparison

Upload a previous and current `.txt` specification.

SpecGuard classifies each requirement as:

- `CHANGED`
- `ADDED`
- `REMOVED`
- `UNCHANGED`

### Similarity-Based Matching

Requirements do not have to be identical to be matched.

SpecGuard uses textual similarity to associate modified requirements before classifying unmatched requirements as additions or removals.

### Exact Change Detection

For changed requirements, SpecGuard identifies the specific words or values that changed.

Example:

```text
Password must contain at least 8 characters
Password must contain at least 12 characters
```

Detected change:

```text
8 → 12
```

Another example:

```text
Session timeout is 30 minutes
Session timeout is 60 minutes
```

Detected change:

```text
30 → 60
```

### Explainable Rule-Based Risk Analysis

SpecGuard assigns a review priority using transparent rules.

| Requirement Change | Review Priority |
|---|---|
| Unchanged | NONE |
| Added | MEDIUM |
| Removed | HIGH |
| Security-sensitive change | HIGH |
| Other changed requirement | MEDIUM |

Security-sensitive keywords currently include terms such as:

```text
password
authentication
login
session
permission
access
```

The classification is intentionally rule-based and explainable.

> A `HIGH` result does not mean a requirement is objectively dangerous or insecure. It means the change matches a rule that suggests it may deserve closer human review.

### Comparison History

The Flask application stores comparison runs in SQLite so previous results can be reopened.

The GitHub Pages version provides browser-based history using local storage.

### CSV Reports

Comparison results can be exported as CSV for further review or documentation.

Reports include information such as:

- status
- previous requirement
- current requirement
- similarity
- detected change
- risk level
- risk reason

### REST API

The Flask application exposes comparison functionality through a JSON API.

```text
POST /api/compare
```

This allows the comparison engine to be used independently of the HTML interface.

---

## Example

### Previous specification

```text
Users must log in with email and password
Password must contain at least 8 characters
Session timeout is 30 minutes
Maximum upload size is 10 MB
Users can download reports
```

### Current specification

```text
Users must log in with email and password
Two-factor authentication is required
Password must contain at least 12 characters
Session timeout is 60 minutes
Maximum upload size is 25 MB
Users can download reports
```

### SpecGuard result

```text
Changed:   3
Added:     1
Removed:   0
Unchanged: 2
```

Examples of detected changes:

```text
8  → 12     HIGH
30 → 60     HIGH
10 → 25     MEDIUM
```

---

## Architecture

SpecGuard contains two interfaces around the requirement comparison logic.

### Full Application

```text
Browser
   |
   v
Flask Application
   |
   +---- Requirement Comparison Engine
   |
   +---- Rule-Based Risk Analysis
   |
   +---- SQLite Comparison History
   |
   +---- CSV Report Generation
   |
   +---- REST API
```

### GitHub Pages Demo

```text
Browser
   |
   v
HTML / CSS / JavaScript
   |
   +---- Browser Comparison Logic
   |
   +---- Change Detail Analysis
   |
   +---- Rule-Based Risk Analysis
   |
   +---- LocalStorage History
   |
   +---- Browser CSV Export
```

GitHub Pages cannot execute the Python/Flask backend, so the public demo performs the comparison directly in the browser.

---

## Technology Stack

**Backend**

- Python
- Flask
- SQLite

**Frontend**

- HTML
- CSS
- JavaScript

**Testing**

- pytest

**Development**

- Git
- GitHub

**Deployment**

- GitHub Pages

---

## Project Structure

```text
SpecGuard/
│
├── app.py
├── comparison.py
├── database.py
├── risk_analysis.py
├── index.html
├── requirements.txt
│
├── templates/
│   ├── index.html
│   ├── results.html
│   └── history.html
│
├── static/
│   ├── style.css
│   └── script.js
│
├── test_app.py
├── test_comparison.py
├── test_risk_analysis.py
│
└── README.md
```

---

## Running SpecGuard Locally

### 1. Clone the repository

```bash
git clone https://github.com/rboddire-source/SpecGuard.git
cd SpecGuard
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Flask application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000/
```

---

## Running the Tests

Run:

```bash
python -m pytest -v
```

Current test suite:

```text
22 passed
```

The tests cover core comparison behavior, change-detail detection, application routes, and risk-analysis rules.

---

## Design Decisions

### Why use similarity matching?

Requirement changes often preserve most of the original sentence.

For example:

```text
Maximum upload size is 10 MB
```

and:

```text
Maximum upload size is 25 MB
```

should normally be interpreted as a modified requirement rather than one removed requirement and one unrelated addition.

Similarity matching allows SpecGuard to associate these requirements before determining their status.

### Why rule-based risk analysis?

The goal is not to predict software risk using an opaque model.

A small rule-based system makes each classification easy to understand and explain. A reviewer can see both the priority and the reason it was assigned.

### Why SQLite?

SpecGuard only needs lightweight local persistence for comparison history. SQLite provides this without requiring a separate database server.

---

## Limitations

SpecGuard currently compares requirements primarily using textual similarity.

This means:

- It does not perform full semantic understanding.
- Reworded requirements with very different wording may not match correctly.
- Greedy similarity matching can produce imperfect matches when several requirements are highly similar.
- Risk levels are review-priority heuristics, not security guarantees or predictions.
- The browser demo and Python implementation use different underlying similarity implementations, so unusual edge cases may produce slightly different matches.

These limitations are intentional and help define clear areas for future improvement.

---

## Possible Future Improvements

Potential extensions include:

- stronger semantic requirement matching
- configurable similarity thresholds
- configurable risk rules
- document formats beyond `.txt`
- richer comparison reports
- multi-user project history
- improved matching for ambiguous requirements

The current version intentionally prioritizes a small, understandable, testable system over unnecessary complexity.

---

## Author

**Rochishna Boddireddy**

M.S. Computer Science — Data Science  
University of North Carolina at Charlotte

GitHub: **rboddire-source**