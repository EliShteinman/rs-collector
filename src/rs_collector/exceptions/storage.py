from rs_collector.exceptions.base import RsCollectorError


class StorageError(RsCollectorError):
    pass


class PackageNotFoundError(StorageError):
    pass


class AnalysisNotFoundError(StorageError):
    pass


class MetadataError(StorageError):
    pass


class ArtifactNotFoundError(StorageError):
    pass
