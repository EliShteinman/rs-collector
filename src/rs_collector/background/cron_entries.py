import shlex
from collections.abc import Mapping
from pathlib import Path

from rs_collector.background.program import Program
from rs_collector.settings.models import BackgroundSettings

_AT_REBOOT = "@reboot"
_START_COMMAND = "start"
_CLEANUP_COMMAND = "cleanup"
_CARRIED_VARIABLES = ("RSC_CONFIG_DIR", "RSC_DATA_ROOT")
_DISCARD_OUTPUT = ">/dev/null 2>&1"
_CRON_PERCENT = "%"
_ESCAPED_PERCENT = "\\%"


class CronEntries:
    def __init__(
        self,
        program: Program,
        settings: BackgroundSettings,
        environment: Mapping[str, str],
        working_dir: Path,
    ) -> None:
        self._program = program
        self._settings = settings
        self._environment = environment
        self._working_dir = working_dir

    def lines(self) -> tuple[str, ...]:
        return (
            self._line(_AT_REBOOT, _START_COMMAND),
            self._line(self._settings.cleanup_schedule, _CLEANUP_COMMAND),
        )

    def _line(self, schedule: str, command: str) -> str:
        return f"{schedule} {self._shell_command(command)} {self._settings.crontab_marker}"

    def _shell_command(self, command: str) -> str:
        parts = (
            f"cd {shlex.quote(str(self._working_dir))} &&",
            *self._assignments(),
            shlex.join(self._program.argv(command)),
            _DISCARD_OUTPUT,
        )
        return " ".join(parts).replace(_CRON_PERCENT, _ESCAPED_PERCENT)

    def _assignments(self) -> tuple[str, ...]:
        return tuple(
            f"{name}={shlex.quote(self._environment[name])}"
            for name in _CARRIED_VARIABLES
            if self._environment.get(name)
        )
