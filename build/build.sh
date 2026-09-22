#!/usr/bin/env bash
# Builds dist/rsc-release.tar.gz on a RHEL 9 x86_64 machine, with no Docker, no root and no
# network: Python and every package come from vendor/.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/.build"
PYTHON_ARCHIVE="${PROJECT_ROOT}/vendor/python/cpython-3.14.7+20260901-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
PYTHON_SHA256="3959f92825141e04adf44982d3a83ee57af0877e893b0796e04c1468749d9b04"
PYTHON="${BUILD_DIR}/python/bin/python3"
VENV="${BUILD_DIR}/venv"
OUTPUT_DIR="${PROJECT_ROOT}/dist"
RELEASE_NAME="rsc-release"
RELEASE_DIR="${OUTPUT_DIR}/${RELEASE_NAME}"

require_linux_x86_64() {
    if [[ "$(uname -s)-$(uname -m)" != "Linux-x86_64" ]]; then
        echo "Build on a RHEL 9 x86_64 machine: the executable matches the system it is built on" >&2
        exit 1
    fi
}

unpack_python() {
    echo "${PYTHON_SHA256}  ${PYTHON_ARCHIVE}" | sha256sum --check --quiet
    rm -rf "${BUILD_DIR}/python"
    mkdir -p "${BUILD_DIR}"
    tar -xzf "${PYTHON_ARCHIVE}" -C "${BUILD_DIR}"
}

install_packages() {
    "${PYTHON}" -m venv --clear "${VENV}"
    "${VENV}/bin/pip" install --quiet --no-index --find-links "${PROJECT_ROOT}/vendor/build-wheels" \
        -r "${PROJECT_ROOT}/vendor/requirements-build.txt"
    "${VENV}/bin/pip" install --quiet --no-index --find-links "${PROJECT_ROOT}/vendor/wheels" \
        -r "${PROJECT_ROOT}/vendor/requirements.txt"
}

build_executable() {
    "${VENV}/bin/pyinstaller" --clean --noconfirm --log-level WARN \
        --distpath "${OUTPUT_DIR}" --workpath "${BUILD_DIR}/pyinstaller" \
        "${PROJECT_ROOT}/build/rsc.spec"
    "${OUTPUT_DIR}/rsc" --help > /dev/null
}

assemble_release() {
    rm -rf "${RELEASE_DIR}"
    mkdir -p "${RELEASE_DIR}"
    cp "${OUTPUT_DIR}/rsc" "${RELEASE_DIR}/rsc"
    cp -R "${PROJECT_ROOT}/config" "${RELEASE_DIR}/config"
    cp "${PROJECT_ROOT}/rsc.env.example" "${RELEASE_DIR}/rsc.env"
    chmod 0600 "${RELEASE_DIR}/rsc.env"
    tar --no-xattrs -czf "${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz" -C "${OUTPUT_DIR}" "${RELEASE_NAME}"
}

require_linux_x86_64
unpack_python
install_packages
build_executable
assemble_release

echo "Built ${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz"
