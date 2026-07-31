import sqlite3
from pathlib import Path

from job_tracker.models import Application


def connect(db_path: str | Path = "data/job_tracker.db") -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            status TEXT NOT NULL,
            applied_date TEXT NOT NULL,
            deadline TEXT,
            notes TEXT NOT NULL DEFAULT ''
        )
        """
    )
    connection.commit()


def add_application(
    connection: sqlite3.Connection,
    application: Application,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO applications (
            company,
            position,
            status,
            applied_date,
            deadline,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            application.company,
            application.position,
            application.status,
            application.applied_date.isoformat(),
            application.deadline.isoformat() if application.deadline else None,
            application.notes,
        ),
    )
    connection.commit()

    if cursor.lastrowid is None:
        raise RuntimeError("Failed to create application.")

    return cursor.lastrowid


def get_applications(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        """
        SELECT
            id,
            company,
            position,
            status,
            applied_date,
            deadline,
            notes
        FROM applications
        ORDER BY applied_date DESC, id DESC
        """
    ).fetchall()

    return [dict(row) for row in rows]


def delete_application(
    connection: sqlite3.Connection,
    application_id: int,
) -> None:
    connection.execute(
        "DELETE FROM applications WHERE id = ?",
        (application_id,),
    )
    connection.commit()


def update_application(
    connection: sqlite3.Connection,
    application_id: int,
    application: Application,
) -> None:
    cursor = connection.execute(
        """
        UPDATE applications
        SET
            company = ?,
            position = ?,
            status = ?,
            applied_date = ?,
            deadline = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            application.company,
            application.position,
            application.status,
            application.applied_date.isoformat(),
            application.deadline.isoformat()
            if application.deadline
            else None,
            application.notes,
            application_id,
        ),
    )
    connection.commit()

    if cursor.rowcount == 0:
        raise ValueError(
            f"Application ID {application_id} was not found."
        )
