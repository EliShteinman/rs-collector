from argparse import ArgumentParser, Namespace, _SubParsersAction
from collections.abc import Sequence

_PROGRAM = "rsc"
_DESCRIPTION = "Collect Redis Enterprise support packages and analyze them with RedisScope"
_COMMAND_DESTINATION = "command"

type Subcommands = _SubParsersAction[ArgumentParser]


class CliParser:
    def parse(self, argv: Sequence[str] | None = None) -> Namespace:
        return self._parser().parse_args(argv)

    def _parser(self) -> ArgumentParser:
        parser = ArgumentParser(prog=_PROGRAM, description=_DESCRIPTION)
        commands = parser.add_subparsers(dest=_COMMAND_DESTINATION, required=True)
        self._add_collect(commands)
        commands.add_parser("analyze", help="Analyze a stored support package")
        commands.add_parser("list", help="List the stored packages and analyses")
        self._add_pinning(commands)
        self._add_cleanup(commands)
        commands.add_parser("serve", help="Serve the analyses over HTTP")
        commands.add_parser(
            "start", help="Run the display server in the background, across logouts and reboots"
        )
        commands.add_parser("stop", help="Stop the display server and its automatic start")
        return parser

    def _add_collect(self, commands: Subcommands) -> None:
        collect = commands.add_parser("collect", help="Collect a support package from a cluster")
        collect.add_argument(
            "--conn-string",
            dest="conn_string",
            default=None,
            help="Database connection string identifying the cluster",
        )

    def _add_pinning(self, commands: Subcommands) -> None:
        for name, help_text in (
            ("pin", "Keep a package or analysis beyond the retention period"),
            ("unpin", "Let a package or analysis expire again"),
        ):
            command = commands.add_parser(name, help=help_text)
            command.add_argument("name", help="Name of the package or analysis")

    def _add_cleanup(self, commands: Subcommands) -> None:
        cleanup = commands.add_parser("cleanup", help="Remove expired packages and analyses")
        cleanup.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Only report what would be removed",
        )
