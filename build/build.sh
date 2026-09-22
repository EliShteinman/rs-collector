#!/usr/bin/env bash
# Builds dist/rsc, the single-file executable for RHEL 9 x86_64.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="rsc-builder:latest"
OUTPUT_DIR="${PROJECT_ROOT}/dist"

cd "${PROJECT_ROOT}"
mkdir -p "${OUTPUT_DIR}"

docker build --platform linux/amd64 -f build/Dockerfile -t "${IMAGE_TAG}" .
docker run --rm --platform linux/amd64 -v "${OUTPUT_DIR}:/out" "${IMAGE_TAG}"

echo "Built ${OUTPUT_DIR}/rsc"
