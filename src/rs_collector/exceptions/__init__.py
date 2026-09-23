from rs_collector.exceptions.analysis import (
    AnalysisError,
    AnalysisFailedError,
    AnalysisTimeoutError,
    AnalyzerStartError,
)
from rs_collector.exceptions.background import (
    BackgroundError,
    CrontabError,
    ServerStartError,
    ServerStopError,
)
from rs_collector.exceptions.base import RsCollectorError
from rs_collector.exceptions.concurrency import (
    CollectionAlreadyRunningError,
    ConcurrencyError,
)
from rs_collector.exceptions.configuration import (
    ConfigFileFormatError,
    ConfigFileNotFoundError,
    ConfigurationError,
    ConfigValidationError,
    MissingCredentialsError,
    MissingSettingError,
)
from rs_collector.exceptions.dblogs import (
    DatabaseLogsError,
    DatabaseNotFoundError,
    NoLogsForDatabaseError,
)
from rs_collector.exceptions.jobs import JobError, JobNotFoundError
from rs_collector.exceptions.privileges import PrivilegeError, RunningAsRootError
from rs_collector.exceptions.processes import (
    ProcessError,
    ProcessStartError,
    ProcessTimeoutError,
)
from rs_collector.exceptions.remote import (
    ClusterUnreachableError,
    DebugInfoOutputError,
    FileTransferError,
    HostKeyMismatchError,
    RemoteCommandError,
    RemoteCommandTimeoutError,
    RemoteError,
    RootEscalationError,
    RootSessionClosedError,
    SshConnectionError,
    TransferIntegrityError,
)
from rs_collector.exceptions.selection import (
    ClusterNotFoundError,
    ConnectionStringError,
    EmptyInventoryError,
    SelectionAbortedError,
    SelectionError,
)
from rs_collector.exceptions.serve import DisplayServerStartError, ServeError
from rs_collector.exceptions.storage import (
    AnalysisNotFoundError,
    ArtifactNotFoundError,
    MetadataError,
    PackageNotFoundError,
    StorageError,
)
from rs_collector.exceptions.web import BadRequestError, RouteNotFoundError, WebError

__all__ = [
    "AnalysisError",
    "AnalysisFailedError",
    "AnalysisNotFoundError",
    "AnalysisTimeoutError",
    "AnalyzerStartError",
    "ArtifactNotFoundError",
    "BackgroundError",
    "BadRequestError",
    "ClusterNotFoundError",
    "ClusterUnreachableError",
    "CollectionAlreadyRunningError",
    "ConcurrencyError",
    "ConfigFileFormatError",
    "ConfigFileNotFoundError",
    "ConfigValidationError",
    "ConfigurationError",
    "ConnectionStringError",
    "CrontabError",
    "DatabaseLogsError",
    "DatabaseNotFoundError",
    "DebugInfoOutputError",
    "DisplayServerStartError",
    "EmptyInventoryError",
    "FileTransferError",
    "HostKeyMismatchError",
    "JobError",
    "JobNotFoundError",
    "MetadataError",
    "MissingCredentialsError",
    "MissingSettingError",
    "NoLogsForDatabaseError",
    "PackageNotFoundError",
    "PrivilegeError",
    "ProcessError",
    "ProcessStartError",
    "ProcessTimeoutError",
    "RemoteCommandError",
    "RemoteCommandTimeoutError",
    "RemoteError",
    "RootEscalationError",
    "RootSessionClosedError",
    "RouteNotFoundError",
    "RsCollectorError",
    "RunningAsRootError",
    "SelectionAbortedError",
    "SelectionError",
    "ServeError",
    "ServerStartError",
    "ServerStopError",
    "SshConnectionError",
    "StorageError",
    "TransferIntegrityError",
    "WebError",
]
