import re

from rs_collector.exceptions.remote import DebugInfoOutputError

_SAVED_FILE_PATTERN = re.compile(r"File\s+(?P<path>\S+)\s+is\s+saved", re.IGNORECASE)
_ARCHIVE_PATTERN = re.compile(r"(?P<path>/\S+\.tar\.gz)")


class DebugInfoOutputParser:
    def package_path(self, output: str) -> str:
        for pattern in (_SAVED_FILE_PATTERN, _ARCHIVE_PATTERN):
            match = self._last_match(pattern, output)
            if match is not None:
                return match.group("path").rstrip(".,")
        raise DebugInfoOutputError(
            f"rladmin did not report a support package path. Output: {output!r}"
        )

    def _last_match(self, pattern: re.Pattern[str], output: str) -> re.Match[str] | None:
        matches = list(pattern.finditer(output))
        return matches[-1] if matches else None
