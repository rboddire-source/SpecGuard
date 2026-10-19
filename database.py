import os
import sqlite3

import psycopg
from psycopg.rows import dict_row


SQLITE_DATABASE_NAME = "specguard.db"


def using_postgres():
    """Return True when the application has a PostgreSQL connection URL."""
    return bool(os.environ.get("DATABASE_URL"))


def get_connection():
    """
    Use PostgreSQL in production when DATABASE_URL exists.
    Otherwise use SQLite for local development.
    """
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg.connect(
            database_url,
            row_factory=dict_row
        )

    connection = sqlite3.connect(SQLITE_DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def placeholder():
    """
    PostgreSQL uses %s placeholders.
    SQLite uses ? placeholders.
    """
    return "%s" if using_postgres() else "?"


def create_database():
    connection = get_connection()
    cursor = connection.cursor()

    if using_postgres():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparison_runs (
                id BIGSERIAL PRIMARY KEY,
                old_filename TEXT NOT NULL,
                new_filename TEXT NOT NULL,
                changed_count INTEGER DEFAULT 0,
                added_count INTEGER DEFAULT 0,
                removed_count INTEGER DEFAULT 0,
                unchanged_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS changes (
                id BIGSERIAL PRIMARY KEY,
                run_id BIGINT NOT NULL,
                status TEXT NOT NULL,
                old_requirement TEXT,
                new_requirement TEXT,
                similarity REAL DEFAULT 0,
                FOREIGN KEY (run_id)
                    REFERENCES comparison_runs(id)
                    ON DELETE CASCADE
            )
        """)

    else:
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

    p = placeholder()

    if using_postgres():
        cursor.execute(f"""
            INSERT INTO comparison_runs (
                old_filename,
                new_filename,
                changed_count,
                added_count,
                removed_count,
                unchanged_count
            )
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
            RETURNING id
        """, (
            old_filename,
            new_filename,
            summary["changed"],
            summary["added"],
            summary["removed"],
            summary["unchanged"]
        ))

        run_id = cursor.fetchone()["id"]

    else:
        cursor.execute(f"""
            INSERT INTO comparison_runs (
                old_filename,
                new_filename,
                changed_count,
                added_count,
                removed_count,
                unchanged_count
            )
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
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
        cursor.execute(f"""
            INSERT INTO changes (
                run_id,
                status,
                old_requirement,
                new_requirement,
                similarity
            )
            VALUES ({p}, {p}, {p}, {p}, {p})
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

    p = placeholder()

    cursor.execute(f"""
        SELECT *
        FROM comparison_runs
        WHERE id = {p}
    """, (run_id,))

    comparison = cursor.fetchone()

    if comparison is None:
        connection.close()
        return None, []

    cursor.execute(f"""
        SELECT *
        FROM changes
        WHERE run_id = {p}
        ORDER BY id
    """, (run_id,))

    changes = cursor.fetchall()

    connection.close()

    return comparison, changes