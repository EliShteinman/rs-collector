from collections.abc import Sequence
from pathlib import Path

from rs_collector.exceptions.serve import DisplayServerStartError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.settings.models import ServeSettings, StorageSettings

_CONFIG_FLAG = "-c"
_HOST_FLAG = "-i"
_PORT_FLAG = "-p"
_VOLUME_FLAG = "-v"
_READ_ONLY_ACCESS = "r"
_PROGRAM_NAME = "copyparty"


class DisplayServerCommandBuilder:
    def __init__(
        self, settings: ServeSettings, storage: StorageSettings, config_file: Path
    ) -> None:
        self._settings = settings
        self._storage = storage
        self._config_file = config_file

    def build(self) -> Sequence[str]:
        return (
            _CONFIG_FLAG,
            str(self._config_file),
            _HOST_FLAG,
            self._settings.host,
            _PORT_FLAG,
            str(self._settings.port),
            _VOLUME_FLAG,
            self._volume(),
        )

    def _volume(self) -> str:
        return f"{self._storage.analyses_dir}:/{self._settings.share_name}:{_READ_ONLY_ACCESS}"


class DisplayServer:
    def __init__(
        self,
        settings: ServeSettings,
        storage: StorageSettings,
        config_file: Path,
    ) -> None:
        self._settings = settings
        self._storage = storage
        self._builder = DisplayServerCommandBuilder(settings, storage, config_file)
        self._logger = LoggerFactory.for_component("serve")

    def start(self) -> None:
        self._storage.analyses_dir.mkdir(parents=True, exist_ok=True)
        argv = list(self._builder.build())
        self._logger.info(
            "Serving %s on %s:%d",
            self._storage.analyses_dir,
            self._settings.host,
            self._settings.port,
        )
        self._run(argv)

    def _run(self, argv: list[str]) -> None:
        try:
            from copyparty.__main__ import main as copyparty_main
        except ImportError as error:
            raise DisplayServerStartError(f"{_PROGRAM_NAME} is not available: {error}") from error
        try:
            copyparty_main(argv=argv)
        except SystemExit as error:
            raise DisplayServerStartError(
                f"{_PROGRAM_NAME} stopped with status {error.code}"
            ) from error
        except OSError as error:
            raise DisplayServerStartError(f"{_PROGRAM_NAME} could not start: {error}") from error
