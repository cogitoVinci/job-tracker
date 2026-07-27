from datetime import date

from job_tracker.database import (
    add_application,
    connect,
    delete_application,
    get_applications,
    initialize_database,
)
from job_tracker.models import Application


def test_add_and_get_application(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    connection = connect(database_path)
    initialize_database(connection)

    application = Application(
        company="Example Company",
        position="Data Analyst",
        status="応募済み",
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
    assert applications[0]["status"] == "応募済み"

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
