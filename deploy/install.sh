#!/usr/bin/env bash
# Installs the rsc collector on a RHEL 9 x86_64 server.
# Run as root from the unpacked release directory:  ./deploy/install.sh
set -euo pipefail

SERVICE_USER="rsc"
INSTALL_ROOT="/opt/rsc"
BINARY_PATH="${INSTALL_ROOT}/bin/rsc"
CONFIG_DIR="/etc/rsc/config"
ENV_FILE="/etc/rsc/rsc.env"
SYSTEMD_DIR="/etc/systemd/system"
RELEASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        echo "This installer must run as root" >&2
        exit 1
    fi
}

create_service_user() {
    if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
        useradd --system --home-dir "${INSTALL_ROOT}" --shell /sbin/nologin "${SERVICE_USER}"
    fi
}

install_binary() {
    install -d -m 0755 "${INSTALL_ROOT}/bin"
    install -m 0755 "${RELEASE_DIR}/dist/rsc" "${BINARY_PATH}"
}

install_configuration() {
    install -d -m 0755 "${CONFIG_DIR}"
    for file in settings.yml clusters.yml logging.yml copyparty.conf; do
        if [[ -f "${CONFIG_DIR}/${file}" ]]; then
            install -m 0644 "${RELEASE_DIR}/config/${file}" "${CONFIG_DIR}/${file}.new"
        else
            install -m 0644 "${RELEASE_DIR}/config/${file}" "${CONFIG_DIR}/${file}"
        fi
    done
    if [[ ! -f "${ENV_FILE}" ]]; then
        install -m 0600 "${RELEASE_DIR}/.env.example" "${ENV_FILE}"
    fi
    chown -R root:"${SERVICE_USER}" /etc/rsc
    chmod 0640 "${ENV_FILE}"
}

install_units() {
    install -m 0644 "${RELEASE_DIR}"/deploy/systemd/*.service "${SYSTEMD_DIR}/"
    install -m 0644 "${RELEASE_DIR}"/deploy/systemd/*.timer "${SYSTEMD_DIR}/"
    systemctl daemon-reload
    systemctl enable --now rsc-cleanup.timer
    systemctl enable rsc-serve.service
}

link_command() {
    ln -sf "${BINARY_PATH}" /usr/local/bin/rsc
    cat > /etc/profile.d/rsc.sh <<PROFILE
export RSC_CONFIG_DIR="${CONFIG_DIR}"
PROFILE
    chmod 0644 /etc/profile.d/rsc.sh
}

require_root
create_service_user
install_binary
install_configuration
install_units
link_command

echo "rsc is installed."
echo "Set RSC_DATA_ROOT and the SSH settings in ${ENV_FILE}, edit ${CONFIG_DIR}/clusters.yml,"
echo "then run: systemctl start rsc-serve.service, and rsc collect"
