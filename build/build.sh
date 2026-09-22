#!/usr/bin/env bash
# Builds dist/rsc-release.tar.gz on a RHEL 9 x86_64 machine, with no Docker and no root.
# Run build/fetch-python.sh once first, or point PYTHON at another Python 3.14.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/.build"
PYTHON="${PYTHON:-${BUILD_DIR}/python/bin/python3}"
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

require_python() {
    if [[ ! -x "${PYTHON}" ]]; then
        echo "No Python at ${PYTHON}. Run build/fetch-python.sh first." >&2
        exit 1
    fi
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
require_python
install_packages
build_executable
assemble_release

echo "Built ${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz"
