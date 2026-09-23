_KILO = 1024
_UNITS = ("B", "KB", "MB", "GB", "TB")


def size(byte_count: int | float) -> str:
    amount = float(byte_count)
    for unit in _UNITS[:-1]:
        if amount < _KILO:
            return f"{amount:.0f} {unit}" if unit in ("B", "KB") else f"{amount:.1f} {unit}"
        amount /= _KILO
    return f"{amount:.1f} {_UNITS[-1]}"
