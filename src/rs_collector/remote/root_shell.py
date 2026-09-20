import re

from pydantic import SecretStr

from rs_collector.exceptions.remote import (
    RemoteCommandError,
    RemoteCommandTimeoutError,
    RootEscalationError,
)
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.channel import ShellChannel
from rs_collector.remote.channel_reader import ChannelReader
from rs_collector.remote.models import CommandResult
from rs_collector.remote.output import CommandOutputCleaner, MarkerFactory
from rs_collector.settings.models import RemoteSettings

_ESCALATION_COMMAND = "sudo su -"
_PASSWORD_PROMPTS = ("assword:", "assword for")
_ROOT_USER_ID = "0"
_IDENTITY_COMMAND = "id -u"
_NEWLINE = "\n"


class RootShell:
    def __init__(
        self,
        channel: ShellChannel,
        reader: ChannelReader,
        settings: RemoteSettings,
        sudo_password: SecretStr | None = None,
        markers: MarkerFactory | None = None,
        cleaner: CommandOutputCleaner | None = None,
    ) -> None:
        self._channel = channel
        self._reader = reader
        self._settings = settings
        self._sudo_password = sudo_password
        self._markers = markers or MarkerFactory()
        self._cleaner = cleaner or CommandOutputCleaner()
        self._logger = LoggerFactory.for_component("remote.root")

    def escalate(self) -> None:
        self._logger.debug("Escalating with '%s'", _ESCALATION_COMMAND)
        self._send_line(_ESCALATION_COMMAND)
        self._answer_password_prompt()
        self._verify_root()
        self._logger.info("Root shell is ready")

    def run(self, command: str, timeout_seconds: int) -> CommandResult:
        marker = self._markers.next()
        self._logger.debug("Running as root: %s", command)
        self._send_line(f"{command}; echo {marker}:$?")
        pattern = re.compile(rf"{re.escape(marker)}:(\d+)")
        raw_output, match = self._read(pattern, timeout_seconds, command)
        return CommandResult(
            command=command,
            exit_status=int(match.group(1)),
            output=self._cleaner.clean(raw_output, command, marker),
        )

    def run_checked(self, command: str, timeout_seconds: int) -> CommandResult:
        result = self.run(command, timeout_seconds)
        if not result.succeeded:
            raise RemoteCommandError(
                f"'{command}' failed with status {result.exit_status}: {result.output}"
            )
        return result

    def _read(
        self, pattern: re.Pattern[str], timeout_seconds: int, command: str
    ) -> tuple[str, re.Match[str]]:
        try:
            return self._reader.read_until_pattern(pattern, timeout_seconds)
        except RemoteCommandTimeoutError as error:
            raise RemoteCommandTimeoutError(
                f"'{command}' did not finish within {timeout_seconds} seconds"
            ) from error

    def _answer_password_prompt(self) -> None:
        if self._sudo_password is None:
            self._logger.debug("No sudo password is configured, expecting passwordless sudo")
            return
        try:
            self._reader.read_until_any(_PASSWORD_PROMPTS, self._settings.sudo_prompt_wait_seconds)
        except RemoteCommandTimeoutError:
            self._logger.debug("No sudo password prompt appeared")
            return
        self._send_line(self._sudo_password.get_secret_value())

    def _verify_root(self) -> None:
        try:
            result = self.run(_IDENTITY_COMMAND, self._settings.root_prompt_timeout_seconds)
        except (RemoteCommandError, RemoteCommandTimeoutError) as error:
            raise RootEscalationError(f"The root shell never became usable: {error}") from error
        if result.first_line() != _ROOT_USER_ID:
            raise RootEscalationError(
                f"'{_ESCALATION_COMMAND}' did not produce a root shell (id -u said "
                f"'{result.first_line()}'). Set RSC_SUDO_PASSWORD if sudo asks for a password."
            )

    def _send_line(self, line: str) -> None:
        self._channel.send(f"{line}{_NEWLINE}")
