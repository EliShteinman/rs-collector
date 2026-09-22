import sys
from pathlib import Path

_PACKAGE_ROOT_DEPTH = 3
_BUNDLE_ATTRIBUTE = "_MEIPASS"


class BundleLocator:
    def __init__(self, module_file: Path | None = None, executable: str = sys.executable) -> None:
        self._module_file = module_file or Path(__file__)
        self._executable = executable

    def root(self) -> Path:
        if self.is_frozen():
            return Path(self._executable).resolve().parent
        return self._module_file.resolve().parents[_PACKAGE_ROOT_DEPTH]

    def is_frozen(self) -> bool:
        return hasattr(sys, _BUNDLE_ATTRIBUTE)
