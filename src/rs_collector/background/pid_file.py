from pathlib import Path

from rs_collector.background.processes import ProcessSignals

_ENCODING = "utf-8"


class PidFile:
    def __init__(self, path: Path, processes: ProcessSignals | None = None) -> None:
        self._path = path
        self._processes = processes or ProcessSignals()

    def running_pid(self) -> int | None:
        pid = self._read()
        if pid is None or not self._processes.is_alive(pid):
            return None
        return pid

    def write(self, pid: int) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(f"{pid}\n", encoding=_ENCODING)

    def remove(self) -> None:
        self._path.unlink(missing_ok=True)

    def _read(self) -> int | None:
        try:
            content = self._path.read_text(encoding=_ENCODING).strip()
        except FileNotFoundError:
            return None
        return int(content) if content.isdigit() else None
