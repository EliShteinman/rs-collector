from typing import Protocol

from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.settings.credentials import WebCredentials
from rs_collector.web.http import Request
from rs_collector.web.security.basic import BasicLogin


class AccessGuard(Protocol):
    def allows(self, request: Request) -> bool: ...


class OpenAccess:
    def allows(self, request: Request) -> bool:  # noqa: ARG002
        return True


class BasicAccess:
    def __init__(self, credentials: WebCredentials) -> None:
        self._credentials = credentials
        self._logger = LoggerFactory.for_component("web.access")

    def allows(self, request: Request) -> bool:
        login = BasicLogin.offered(request.headers)
        if login is None:
            self._logger.debug("%s %s arrived without a login", request.method, request.path)
            return False
        if not self._credentials.matches(login.user, login.password):
            self._logger.warning("Refused %s on %s", login.user, request.path)
            return False
        self._logger.debug("Allowed %s on %s", login.user, request.path)
        return True


def access_guard(credentials: WebCredentials) -> AccessGuard:
    if credentials.validated().demanded:
        return BasicAccess(credentials)
    LoggerFactory.for_component("web.access").warning(
        "The web interface asks for no login: set RSC_WEB_USER and RSC_WEB_PASSWORD to protect it"
    )
    return OpenAccess()
