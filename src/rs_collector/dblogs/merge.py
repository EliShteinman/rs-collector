import gzip
from collections.abc import Iterator, Sequence
from pathlib import Path

from rs_collector.dblogs.models import LogFile, MergedLog
from rs_collector.dblogs.timestamps import first_moment
from rs_collector.logging_setup.configurator import LoggerFactory

_ENCODING = "utf-8"
_NEWLINE = "\n"
_SOURCE_MARK = "===== {name} ({node}) ====="


class LogMerger:
    def __init__(self, mark_sources: bool = True) -> None:
        self._mark_sources = mark_sources
        self._logger = LoggerFactory.for_component("dblogs.merge")

    def merge(
        self, title: str, sources: Sequence[LogFile], target: Path, node: str = "", role: str = ""
    ) -> MergedLog:
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = 0
        first = None
        last = None
        with target.open("w", encoding=_ENCODING, newline="") as merged:
            for source in _ordered(sources):
                if self._mark_sources:
                    merged.write(
                        _SOURCE_MARK.format(name=source.path.name, node=source.node or "-")
                        + _NEWLINE
                    )
                for line in _lines(source):
                    merged.write(line + _NEWLINE)
                    lines += 1
                    moment = first_moment(line)
                    if moment is not None:
                        first = first or moment
                        last = moment
        self._logger.info("Merged %d files into %s", len(sources), target)
        return MergedLog(
            title=title,
            path=target,
            sources=tuple(source.path for source in sources),
            lines=lines,
            byte_count=target.stat().st_size,
            node=node,
            role=role,
            first_seen=first,
            last_seen=last,
        )


def _ordered(sources: Sequence[LogFile]) -> list[LogFile]:
    return sorted(sources, key=lambda item: (item.node, -item.rotation, item.path.name))


def _lines(source: LogFile) -> Iterator[str]:
    opener = gzip.open if source.compressed else open
    try:
        with opener(source.path, "rt", encoding=_ENCODING, errors="replace") as stream:
            for line in stream:
                yield line.rstrip(_NEWLINE)
    except (OSError, EOFError) as error:
        yield f"===== {source.path.name} could not be read: {error} ====="
