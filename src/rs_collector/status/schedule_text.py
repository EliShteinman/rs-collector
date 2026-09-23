import re

_DAILY = re.compile(r"^(?P<minute>\d{1,2}) (?P<hour>\d{1,2}) \* \* \*$")


def spoken(schedule: str) -> str:
    match = _DAILY.fullmatch(schedule.strip())
    if match is None:
        return schedule
    return f"daily at {int(match.group('hour')):02d}:{int(match.group('minute')):02d}"
