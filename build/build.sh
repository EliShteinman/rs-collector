#!/usr/bin/env bash
# Builds dist/rsc-release.tar.gz: the rsc executable for RHEL 9 x86_64 with its configuration.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="rsc-builder:latest"
OUTPUT_DIR="${PROJECT_ROOT}/dist"
RELEASE_NAME="rsc-release"
RELEASE_DIR="${OUTPUT_DIR}/${RELEASE_NAME}"

cd "${PROJECT_ROOT}"
mkdir -p "${OUTPUT_DIR}"

docker build --platform linux/amd64 -f build/Dockerfile -t "${IMAGE_TAG}" .
docker run --rm --platform linux/amd64 -v "${OUTPUT_DIR}:/out" "${IMAGE_TAG}"

rm -rf "${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}"
cp "${OUTPUT_DIR}/rsc" "${RELEASE_DIR}/rsc"
cp -R config "${RELEASE_DIR}/config"
cp rsc.env.example "${RELEASE_DIR}/rsc.env"
chmod 0600 "${RELEASE_DIR}/rsc.env"
COPYFILE_DISABLE=1 tar --no-xattrs -czf "${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz" -C "${OUTPUT_DIR}" "${RELEASE_NAME}"

echo "Built ${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz"
