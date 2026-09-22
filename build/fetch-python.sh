#!/usr/bin/env bash
# Downloads a ready-made Python 3.14 for Linux x86_64 into .build/python. Needs no root.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20260901/cpython-3.14.7%2B20260901-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
PYTHON_SHA256="3959f92825141e04adf44982d3a83ee57af0877e893b0796e04c1468749d9b04"
BUILD_DIR="${PROJECT_ROOT}/.build"
ARCHIVE="${BUILD_DIR}/python.tar.gz"

mkdir -p "${BUILD_DIR}"
curl -fsSL -o "${ARCHIVE}" "${PYTHON_URL}"
echo "${PYTHON_SHA256}  ${ARCHIVE}" | sha256sum --check --quiet
rm -rf "${BUILD_DIR}/python"
tar -xzf "${ARCHIVE}" -C "${BUILD_DIR}"
rm -f "${ARCHIVE}"

"${BUILD_DIR}/python/bin/python3" --version
