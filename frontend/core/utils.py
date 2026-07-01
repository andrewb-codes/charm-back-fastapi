from datetime import datetime


def parse_birthdate(value: str) -> str | None:
    if not value:
        return None

    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue

    raise ValueError("Use YYYY-MM-DD or DD.MM.YYYY format.")
