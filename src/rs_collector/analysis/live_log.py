import threading
from pathlib import Path

from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.processes.runner import LineReader
from rs_collector.runtime.clock import Clock, SystemClock

_ENCODING = "utf-8"
_NEWLINE = "\n"


class LiveLogFollower:
    def __init__(
        self,
        path: Path,
        on_line: LineReader,
        poll_interval_seconds: float,
        clock: Clock | None = None,
    ) -> None:
        self._path = path
        self._on_line = on_line
        self._poll_interval_seconds = poll_interval_seconds
        self._clock = clock or SystemClock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._follow, daemon=True)
        self._position = 0
        self._pending = ""
        self._logger = LoggerFactory.for_component("analysis.live_log")

    def __enter__(self) -> LiveLogFollower:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=self._poll_interval_seconds * 4)
        self._read_new_lines()

    def _follow(self) -> None:
        while not self._stop.is_set():
            self._read_new_lines()
            self._clock.sleep(self._poll_interval_seconds)

    def _read_new_lines(self) -> None:
        try:
            with self._path.open(encoding=_ENCODING, errors="replace") as stream:
                stream.seek(self._position)
                text = stream.read()
                self._position = stream.tell()
        except OSError:
            return
        self._pending = self._emitted(self._pending + text)

    def _emitted(self, buffered: str) -> str:
        while _NEWLINE in buffered:
            line, buffered = buffered.split(_NEWLINE, maxsplit=1)
            if line:
                self._on_line(line, False)
        return buffered
