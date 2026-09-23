import subprocess
from collections.abc import Sequence
from typing import Protocol

from rs_collector.exceptions.background import CrontabError
from rs_collector.logging_setup.configurator import LoggerFactory

_CRONTAB = "crontab"
_LIST_FLAG = "-l"
_STANDARD_INPUT = "-"
_EMPTY_CRONTAB_MESSAGE = "no crontab"
_NEWLINE = "\n"


class CrontabClient(Protocol):
    def read(self) -> str: ...

    def write(self, content: str) -> None: ...


class SystemCrontab:
    def read(self) -> str:
        result = self._run((_CRONTAB, _LIST_FLAG), content=None)
        if result.returncode == 0:
            return result.stdout
        if _EMPTY_CRONTAB_MESSAGE in result.stderr:
            return ""
        raise CrontabError(f"The crontab cannot be read: {result.stderr.strip()}")

    def write(self, content: str) -> None:
        result = self._run((_CRONTAB, _STANDARD_INPUT), content=content)
        if result.returncode != 0:
            raise CrontabError(f"The crontab cannot be written: {result.stderr.strip()}")

    def _run(self, argv: Sequence[str], content: str | None) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                list(argv), input=content, capture_output=True, text=True, check=False
            )
        except OSError as error:
            raise CrontabError(f"The crontab command cannot be used: {error}") from error


class CrontabInstaller:
    def __init__(self, client: CrontabClient, marker: str) -> None:
        self._client = client
        self._marker = marker
        self._logger = LoggerFactory.for_component("background.crontab")

    def install(self, lines: Sequence[str]) -> None:
        kept = self._foreign_lines(self._client.read())
        self._client.write(self._joined((*kept, *lines)))
        self._logger.info("Installed %d crontab lines", len(lines))

    def installed(self) -> bool:
        return any(self._is_ours(line) for line in self._client.read().splitlines())

    def remove(self) -> bool:
        current = self._client.read()
        kept = self._foreign_lines(current)
        if len(kept) == len(current.splitlines()):
            return False
        self._client.write(self._joined(kept))
        self._logger.info("Removed the rsc crontab lines")
        return True

    def _foreign_lines(self, content: str) -> tuple[str, ...]:
        return tuple(line for line in content.splitlines() if not self._is_ours(line))

    def _is_ours(self, line: str) -> bool:
        return line.rstrip().endswith(self._marker)

    def _joined(self, lines: Sequence[str]) -> str:
        return _NEWLINE.join(lines) + _NEWLINE if lines else ""
