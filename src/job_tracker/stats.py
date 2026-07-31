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
    application_list = [
        application
        for application in applications
        if application["status"] != "検討中"
    ]

    if not application_list:
        return 0.0

    successful_count = sum(
        application["status"] == "内定"
        for application in application_list
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
