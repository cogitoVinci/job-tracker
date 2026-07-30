from job_tracker.stats import (
    calculate_success_rate,
    calculate_total,
    count_by_status,
    count_upcoming_deadlines,
)


def test_count_by_status() -> None:
    applications = [
        {"status": "ES"},
        {"status": "面接"},
        {"status": "面接"},
    ]

    assert count_by_status(applications) == {
        "ES": 1,
        "面接": 2,
    }


def test_calculate_total() -> None:
    applications = [
        {"status": "ES"},
        {"status": "面接"},
    ]

    assert calculate_total(applications) == 2


def test_calculate_success_rate() -> None:
    applications = [
        {"status": "内定"},
        {"status": "不合格"},
        {"status": "内定"},
        {"status": "面接"},
    ]

    assert calculate_success_rate(applications) == 0.5


def test_calculate_success_rate_empty() -> None:
    assert calculate_success_rate([]) == 0.0


def test_count_upcoming_deadlines() -> None:
    applications = [
        {"deadline": "2026-07-30"},
        {"deadline": "2026-07-20"},
        {"deadline": None},
    ]

    assert count_upcoming_deadlines(applications, "2026-07-28") == 1
