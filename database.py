
import json
import os
import sqlite3
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


SQLITE_DATABASE_NAME = "specguard.db"


def using_postgres():
    return bool(os.environ.get("DATABASE_URL"))


def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg.connect(
            database_url,
            row_factory=dict_row,
            sslmode="require"
        )

    connection = sqlite3.connect(SQLITE_DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def placeholder():
    return "%s" if using_postgres() else "?"


@contextmanager
def database_session():
    connection = get_connection()

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_database():
    with database_session() as connection:
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

        # Safe schema migration for existing databases.
        if using_postgres():
            cursor.execute("""
                ALTER TABLE changes
                ADD COLUMN IF NOT EXISTS change_details TEXT
            """)
        else:
            cursor.execute("PRAGMA table_info(changes)")
            columns = {
                row["name"]
                for row in cursor.fetchall()
            }

            if "change_details" not in columns:
                cursor.execute("""
                    ALTER TABLE changes
                    ADD COLUMN change_details TEXT
                """)


def save_comparison(
    old_filename,
    new_filename,
    results,
    summary
):
    with database_session() as connection:
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
            change_details = json.dumps(
                result.get("changes", {
                    "removed": [],
                    "added": []
                })
            )

            cursor.execute(f"""
                INSERT INTO changes (
                    run_id,
                    status,
                    old_requirement,
                    new_requirement,
                    similarity,
                    change_details
                )
                VALUES ({p}, {p}, {p}, {p}, {p}, {p})
            """, (
                run_id,
                result["status"],
                result.get("old"),
                result.get("new"),
                result.get("similarity", 0),
                change_details
            ))

    return run_id


def get_history():
    with database_session() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM comparison_runs
            ORDER BY created_at DESC, id DESC
        """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


def get_comparison(run_id):
    with database_session() as connection:
        cursor = connection.cursor()
        p = placeholder()

        cursor.execute(f"""
            SELECT *
            FROM comparison_runs
            WHERE id = {p}
        """, (run_id,))

        comparison = cursor.fetchone()

        if comparison is None:
            return None, []

        cursor.execute(f"""
            SELECT *
            FROM changes
            WHERE run_id = {p}
            ORDER BY id
        """, (run_id,))

        changes = []

        for row in cursor.fetchall():
            change = dict(row)

            raw_details = change.get("change_details")

            if raw_details:
                try:
                    change["changes"] = json.loads(
                        raw_details
                    )
                except (ValueError, TypeError):
                    change["changes"] = None
            else:
                change["changes"] = None

            changes.append(change)

        return dict(comparison), changes
