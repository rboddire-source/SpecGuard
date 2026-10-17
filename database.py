import sqlite3


DATABASE_NAME = "specguard.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_connection()
    cursor = connection.cursor()

    # One row represents one complete comparison.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparison_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_filename TEXT NOT NULL,
            new_filename TEXT NOT NULL,
            changed_count INTEGER DEFAULT 0,
            added_count INTEGER DEFAULT 0,
            removed_count INTEGER DEFAULT 0,
            unchanged_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Individual requirement changes belong to a comparison run.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            old_requirement TEXT,
            new_requirement TEXT,
            similarity REAL DEFAULT 0,
            FOREIGN KEY (run_id)
                REFERENCES comparison_runs(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


def save_comparison(
    old_filename,
    new_filename,
    results,
    summary
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO comparison_runs (
            old_filename,
            new_filename,
            changed_count,
            added_count,
            removed_count,
            unchanged_count
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        old_filename,
        new_filename,
        summary["changed"],
        summary["added"],
        summary["removed"],
        summary["unchanged"]
    ))

    run_id = cursor.lastrowid

    for result in results:
        cursor.execute("""
            INSERT INTO changes (
                run_id,
                status,
                old_requirement,
                new_requirement,
                similarity
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            run_id,
            result["status"],
            result["old"],
            result["new"],
            result.get("similarity", 0)
        ))

    connection.commit()
    connection.close()

    return run_id


def get_history():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM comparison_runs
        ORDER BY created_at DESC, id DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    return rows


def get_comparison(run_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM comparison_runs
        WHERE id = ?
    """, (run_id,))

    comparison = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM changes
        WHERE run_id = ?
        ORDER BY id
    """, (run_id,))

    changes = cursor.fetchall()

    connection.close()

    return comparison, changes