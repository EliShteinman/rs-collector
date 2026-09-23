from datetime import UTC, datetime

_MINUTE = 60
_HOUR = 3600
_DAY = 86400
_TIMESTAMP = "%Y-%m-%d %H:%M"


def stamp(moment: datetime) -> str:
    return moment.astimezone().strftime(_TIMESTAMP)


def ago(moment: datetime, now: datetime | None = None) -> str:
    seconds = ((now or datetime.now(UTC)) - moment).total_seconds()
    if seconds < _MINUTE:
        return "just now"
    if seconds < _HOUR:
        return _counted(seconds / _MINUTE, "minute")
    if seconds < _DAY:
        return _counted(seconds / _HOUR, "hour")
    return _counted(seconds / _DAY, "day")


def _counted(amount: float, unit: str) -> str:
    whole = int(amount)
    return f"{whole} {unit} ago" if whole == 1 else f"{whole} {unit}s ago"
