import mimetypes
from pathlib import Path

_TEXT = "text/plain; charset=utf-8"
_HTML = "text/html; charset=utf-8"
_DEFAULT = "application/octet-stream"
_CHARSET = "utf-8"
_GZIP_SUFFIX = ".gz"
_LOG_SUFFIXES = (".log", ".out", ".err")
_TEXT_SUFFIXES = (
    ".log",
    ".txt",
    ".csv",
    ".json",
    ".yml",
    ".yaml",
    ".conf",
    ".cfg",
    ".ini",
    ".md",
    ".sh",
    ".out",
    ".err",
)


def is_compressed(path: Path) -> bool:
    return path.suffix == _GZIP_SUFFIX


def uncompressed_name(path: Path) -> Path:
    return path.with_suffix("") if is_compressed(path) else path


def content_type(path: Path) -> str:
    name = uncompressed_name(path)
    if _kind(name) in _TEXT_SUFFIXES:
        return _TEXT
    guessed, _ = mimetypes.guess_type(name.name)
    if guessed is None:
        return _DEFAULT
    if guessed == "text/html":
        return _HTML
    if guessed.startswith("text/"):
        return f"{guessed}; charset={_CHARSET}"
    return guessed


def _kind(name: Path) -> str:
    for suffix in reversed(name.suffixes):
        lowered = suffix.lower()
        if not lowered[1:].isdigit():
            return lowered
    return ""


def is_readable_text(path: Path) -> bool:
    return content_type(path) in (_TEXT, _HTML)


def is_log(path: Path) -> bool:
    return _kind(uncompressed_name(path)) in _LOG_SUFFIXES
