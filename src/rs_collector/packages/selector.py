from rs_collector.console.choice import ChoicePrompt
from rs_collector.exceptions.storage import PackageNotFoundError
from rs_collector.packages.models import StoredPackage
from rs_collector.packages.repository import PackageRepository

_TITLE = "Select a support package:"
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class InteractivePackageSelector:
    def __init__(self, repository: PackageRepository, prompt: ChoicePrompt) -> None:
        self._repository = repository
        self._prompt = prompt

    def select(self) -> StoredPackage:
        packages = self._repository.list()
        if not packages:
            raise PackageNotFoundError("No support package is stored yet")
        index = self._prompt.select(_TITLE, tuple(self._label(p) for p in packages))
        return packages[index]

    def _label(self, package: StoredPackage) -> str:
        metadata = package.metadata
        collected = metadata.collected_at.strftime(_TIMESTAMP_FORMAT)
        return f"{metadata.cluster_fqdn}  {collected}  ({metadata.size_bytes / 1_048_576:.1f} MiB)"
