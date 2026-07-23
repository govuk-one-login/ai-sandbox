#!/bin/sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="di-kiro-android:latest"
TAR_FILE="${SCRIPT_DIR}/di-kiro-android.tar"

echo "Building image..."
docker build --platform linux/arm64 -t "$IMAGE_NAME" "$SCRIPT_DIR"

echo "Exporting image..."
docker image save "$IMAGE_NAME" -o "$TAR_FILE"

echo "Loading into sandbox runtime..."
sbx template load "$TAR_FILE"

echo "Cleaning up tar..."
rm -f "$TAR_FILE"

echo "Done. Run the sandbox with:"
echo "  sbx run di-kiro . --kit path/to/di-kit"
