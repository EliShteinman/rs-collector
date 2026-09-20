from collections.abc import Sequence
from pathlib import Path

from rs_collector.analysis.options import AnalysisOptions

_SUPPORT_PACKAGE_FLAG = "--sp"


class RedisScopeCommandBuilder:
    def __init__(self, binary: Path) -> None:
        self._binary = binary

    def build(self, archive_path: Path, options: AnalysisOptions) -> Sequence[str]:
        return (str(self._binary), _SUPPORT_PACKAGE_FLAG, str(archive_path), *options.flags)
