from collections import Counter
from collections.abc import Iterable


def count_by_status(applications: Iterable[dict]) -> dict[str, int]:
    counter = Counter(
        application["status"]
        for application in applications
    )
    return dict(counter)


def calculate_total(applications: Iterable[dict]) -> int:
    return sum(1 for _ in applications)


def calculate_success_rate(applications: Iterable[dict]) -> float:
    application_list = list(applications)

    if not application_list:
        return 0.0

    successful_statuses = {"内定"}

    successful_count = sum(
        1
        for application in application_list
        if application["status"] in successful_statuses
    )

    return successful_count / len(application_list)


def count_upcoming_deadlines(
    applications: Iterable[dict],
    today: str,
) -> int:
    return sum(
        1
        for application in applications
        if application.get("deadline")
        and application["deadline"] >= today
    )
