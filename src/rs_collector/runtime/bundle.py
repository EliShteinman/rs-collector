import sys
from pathlib import Path

_PACKAGE_ROOT_DEPTH = 3
_BUNDLE_ATTRIBUTE = "_MEIPASS"


class BundleLocator:
    def __init__(self, module_file: Path | None = None) -> None:
        self._module_file = module_file or Path(__file__)

    def root(self) -> Path:
        bundle_dir = getattr(sys, _BUNDLE_ATTRIBUTE, None)
        if bundle_dir is not None:
            return Path(bundle_dir)
        return self._module_file.resolve().parents[_PACKAGE_ROOT_DEPTH]

    def is_frozen(self) -> bool:
        return hasattr(sys, _BUNDLE_ATTRIBUTE)
