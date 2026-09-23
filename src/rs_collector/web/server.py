import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from rs_collector.exceptions.serve import DisplayServerStartError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.settings.models import ServeSettings
from rs_collector.web.application import WebApplication
from rs_collector.web.http import Request

_CONTENT_LENGTH = "Content-Length"
_MAX_BODY_BYTES = 1_048_576
_SERVER_NAME = "rsc"
_SHUTDOWN_TIMEOUT_SECONDS = 5


class WebServer:
    def __init__(self, application: WebApplication, settings: ServeSettings) -> None:
        self._application = application
        self._settings = settings
        self._logger = LoggerFactory.for_component("web.server")

    def serve_forever(self) -> None:
        server = self._server()
        self._logger.info("Serving on http://%s:%d/", self._settings.host, self._settings.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self._logger.info("Stopping the display server")
        finally:
            server.server_close()

    @contextmanager
    def running(self) -> Iterator[int]:
        server = self._server()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield int(server.server_address[1])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=_SHUTDOWN_TIMEOUT_SECONDS)

    def _server(self) -> ThreadingHTTPServer:
        try:
            return ThreadingHTTPServer(
                (self._settings.host, self._settings.port), self._handler_class()
            )
        except OSError as error:
            raise DisplayServerStartError(
                f"The display server cannot listen on "
                f"{self._settings.host}:{self._settings.port}: {error}"
            ) from error

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        application = self._application
        base_path = self._settings.base_path
        logger = self._logger

        class Handler(BaseHTTPRequestHandler):
            server_version = _SERVER_NAME
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:
                self._respond(b"")

            def do_POST(self) -> None:
                self._respond(self._body())

            def log_message(self, format: str, *args: object) -> None:  # noqa: A002
                logger.debug("%s %s", self.address_string(), format % args)

            def _body(self) -> bytes:
                length = min(int(self.headers.get(_CONTENT_LENGTH, 0)), _MAX_BODY_BYTES)
                return self.rfile.read(length) if length else b""

            def _respond(self, body: bytes) -> None:
                parts = urlsplit(self.path)
                response = application.handle(
                    Request.parse(
                        method=self.command or "",
                        path=parts.path,
                        query_string=parts.query,
                        body=body,
                        headers=dict(self.headers.items()),
                        base_path=base_path,
                    )
                )
                self.send_response(response.status)
                self.send_header("Content-Type", response.content_type)
                self.send_header(_CONTENT_LENGTH, str(len(response.body)))
                for name, value in response.headers.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(response.body)

        return Handler
