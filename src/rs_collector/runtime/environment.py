import os
import sys
from collections.abc import Mapping

_BUNDLE_PREFIX = "_PYI"
_BUNDLE_ATTRIBUTE = "_MEIPASS"
_LIBRARY_PATH = "LD_LIBRARY_PATH"
_ORIGINAL_LIBRARY_PATH = "LD_LIBRARY_PATH_ORIG"


class SpawnEnvironment:
    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = dict(environ if environ is not None else os.environ)

    def for_a_new_process(self) -> dict[str, str]:
        cleaned = {
            name: value
            for name, value in self._environ.items()
            if not name.startswith(_BUNDLE_PREFIX)
        }
        return self._with_library_path(cleaned)

    def _with_library_path(self, cleaned: dict[str, str]) -> dict[str, str]:
        original = cleaned.pop(_ORIGINAL_LIBRARY_PATH, None)
        if original is not None:
            cleaned[_LIBRARY_PATH] = original
            return cleaned
        bundle = getattr(sys, _BUNDLE_ATTRIBUTE, None)
        if bundle is not None and cleaned.get(_LIBRARY_PATH) == bundle:
            cleaned.pop(_LIBRARY_PATH)
        return cleaned
