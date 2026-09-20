import hashlib
from pathlib import Path

from rs_collector.exceptions.storage import ArtifactNotFoundError

_ALGORITHM = "sha256"
_CHUNK_SIZE = 1024 * 1024


class FileDigest:
    def of(self, path: Path) -> str:
        digest = hashlib.new(_ALGORITHM)
        try:
            with path.open("rb") as stream:
                while chunk := stream.read(_CHUNK_SIZE):
                    digest.update(chunk)
        except OSError as error:
            raise ArtifactNotFoundError(f"{path} cannot be read: {error}") from error
        return digest.hexdigest()
