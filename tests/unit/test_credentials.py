from pathlib import Path

import pytest

from rs_collector.exceptions.configuration import MissingCredentialsError
from rs_collector.settings.credentials import SshCredentials

pytestmark = pytest.mark.unit


def test_credentials_are_read_from_the_given_env_file(
    tmp_path: Path, clean_environment: None
) -> None:
    env_file = tmp_path / "rsc.env"
    env_file.write_text("RSC_SSH_USER=svc_redis\nRSC_SSH_PASSWORD=secret\n", encoding="utf-8")

    assert SshCredentials.load(env_file).ssh_user == "svc_redis"


def test_the_environment_wins_over_the_env_file(
    tmp_path: Path, clean_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / "rsc.env"
    env_file.write_text("RSC_SSH_USER=from_file\n", encoding="utf-8")
    monkeypatch.setenv("RSC_SSH_USER", "from_environment")

    assert SshCredentials.load(env_file).ssh_user == "from_environment"


def test_a_password_is_kept_secret_in_the_representation(clean_environment: None) -> None:
    credentials = SshCredentials(ssh_user="admin", ssh_password="secret")

    assert "secret" not in repr(credentials)


def test_a_key_path_satisfies_the_validation(tmp_path: Path, clean_environment: None) -> None:
    credentials = SshCredentials(ssh_user="admin", ssh_key_path=tmp_path / "id_ed25519")

    assert credentials.validated().has_key()


def test_a_missing_user_is_reported(clean_environment: None) -> None:
    with pytest.raises(MissingCredentialsError):
        SshCredentials(ssh_password="secret").validated()


def test_missing_authentication_is_reported(clean_environment: None) -> None:
    with pytest.raises(MissingCredentialsError):
        SshCredentials(ssh_user="admin").validated()
