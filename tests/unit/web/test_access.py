from base64 import b64encode

import pytest

from rs_collector.exceptions.configuration import MissingCredentialsError
from rs_collector.settings.credentials import WebCredentials
from rs_collector.web.http import Request
from rs_collector.web.security.access import BasicAccess, OpenAccess, access_guard
from rs_collector.web.security.basic import BasicLogin
from rs_collector.web.security.challenge import challenge

pytestmark = pytest.mark.unit

_CHALLENGE_HEADER = "WWW-Authenticate"


def _credentials() -> WebCredentials:
    return WebCredentials(web_user="ops", web_password="letmein")


def _header(user: str, password: str) -> str:
    return "Basic " + b64encode(f"{user}:{password}".encode()).decode()


def _request(authorization: str | None = None) -> Request:
    headers = {"Authorization": authorization} if authorization is not None else {}
    return Request.parse("GET", "/", headers=headers)


def test_a_login_is_read_from_the_header() -> None:
    assert BasicLogin.offered({"authorization": _header("ops", "letmein")}) == BasicLogin(
        user="ops", password="letmein"
    )


def test_a_password_holding_a_colon_stays_whole() -> None:
    login = BasicLogin.offered({"authorization": _header("ops", "a:b:c")})

    assert login is not None
    assert login.password == "a:b:c"


def test_a_missing_header_offers_no_login() -> None:
    assert BasicLogin.offered({}) is None


def test_another_scheme_offers_no_login() -> None:
    assert BasicLogin.offered({"authorization": "Bearer abcdef"}) is None


def test_text_that_is_not_base64_offers_no_login() -> None:
    assert BasicLogin.offered({"authorization": "Basic not-base-64!"}) is None


def test_a_pair_without_a_colon_offers_no_login() -> None:
    encoded = b64encode(b"opsletmein").decode()

    assert BasicLogin.offered({"authorization": f"Basic {encoded}"}) is None


def test_the_matching_login_is_allowed() -> None:
    guard = BasicAccess(_credentials())

    assert guard.allows(_request(_header("ops", "letmein"))) is True


def test_a_wrong_password_is_refused() -> None:
    guard = BasicAccess(_credentials())

    assert guard.allows(_request(_header("ops", "guess"))) is False


def test_a_wrong_user_is_refused() -> None:
    guard = BasicAccess(_credentials())

    assert guard.allows(_request(_header("someone", "letmein"))) is False


def test_a_request_without_a_login_is_refused() -> None:
    guard = BasicAccess(_credentials())

    assert guard.allows(_request()) is False


def test_credentials_without_a_password_match_nothing() -> None:
    guard = BasicAccess(WebCredentials(web_user="ops"))

    assert guard.allows(_request(_header("ops", ""))) is False


def test_both_variables_ask_for_a_login() -> None:
    assert isinstance(access_guard(_credentials()), BasicAccess)


def test_neither_variable_leaves_the_interface_open() -> None:
    assert isinstance(access_guard(WebCredentials()), OpenAccess)


def test_an_open_interface_allows_every_request() -> None:
    assert OpenAccess().allows(_request()) is True


@pytest.mark.parametrize(
    "credentials",
    [WebCredentials(web_user="ops"), WebCredentials(web_password="letmein")],
)
def test_one_variable_alone_is_a_configuration_error(credentials: WebCredentials) -> None:
    with pytest.raises(MissingCredentialsError):
        access_guard(credentials)


def test_the_challenge_asks_the_browser_for_a_login() -> None:
    response = challenge(_request(), "rsc")

    assert response.status == 401


def test_the_challenge_names_the_realm() -> None:
    response = challenge(_request(), "rsc")

    assert response.headers[_CHALLENGE_HEADER] == 'Basic realm="rsc", charset="UTF-8"'
