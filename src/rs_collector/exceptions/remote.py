from rs_collector.exceptions.base import RsCollectorError


class RemoteError(RsCollectorError):
    pass


class SshConnectionError(RemoteError):
    pass


class ClusterUnreachableError(RemoteError):
    pass


class RootEscalationError(RemoteError):
    pass


class RemoteCommandError(RemoteError):
    pass


class RemoteCommandTimeoutError(RemoteError):
    pass


class DebugInfoOutputError(RemoteError):
    pass


class FileTransferError(RemoteError):
    pass


class TransferIntegrityError(FileTransferError):
    pass
