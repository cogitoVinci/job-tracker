from datetime import date

from job_tracker.database import (
    add_application,
    connect,
    delete_application,
    get_applications,
    initialize_database,
    update_application,
)
from job_tracker.models import Application


def test_add_and_get_application(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    connection = connect(database_path)
    initialize_database(connection)

    application = Application(
        company="Example Company",
        position="Data Analyst",
        status="ES",
        applied_date=date(2026, 7, 28),
        deadline=date(2026, 8, 10),
        notes="Test application",
    )

    application_id = add_application(connection, application)
    applications = get_applications(connection)

    assert application_id == 1
    assert len(applications) == 1
    assert applications[0]["company"] == "Example Company"
    assert applications[0]["position"] == "Data Analyst"
    assert applications[0]["status"] == "ES"

    connection.close()


def test_delete_application(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    connection = connect(database_path)
    initialize_database(connection)

    application = Application(
        company="Delete Company",
        position="Engineer",
        status="面接",
        applied_date=date(2026, 7, 28),
    )

    application_id = add_application(connection, application)
    delete_application(connection, application_id)

    assert get_applications(connection) == []

    connection.close()


def test_update_application(tmp_path) -> None:
    database_path = tmp_path / "test_update.db"
    connection = connect(database_path)
    initialize_database(connection)

    original = Application(
        company="Original Company",
        position="Engineer",
        status="ES",
        applied_date=date(2026, 7, 31),
    )
    application_id = add_application(connection, original)

    updated = Application(
        company="Updated Company",
        position="Data Analyst",
        status="面接",
        applied_date=date(2026, 8, 1),
        deadline=date(2026, 8, 10),
        notes="一次面接",
    )

    update_application(
        connection,
        application_id,
        updated,
    )

    applications = get_applications(connection)

    assert len(applications) == 1
    assert applications[0]["company"] == "Updated Company"
    assert applications[0]["position"] == "Data Analyst"
    assert applications[0]["status"] == "面接"
    assert applications[0]["applied_date"] == "2026-08-01"
    assert applications[0]["deadline"] == "2026-08-10"
    assert applications[0]["notes"] == "一次面接"

    connection.close()
