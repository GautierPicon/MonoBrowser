#!/usr/bin/env bash
set -euo pipefail

rm -rf dist build

ICONSET_DIR="$(mktemp -d)"
trap 'rm -rf "$ICONSET_DIR"' EXIT

mkdir -p "$ICONSET_DIR/icon.iconset"
sips -z 16 16 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_16x16.png"
sips -z 32 32 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_16x16@2x.png"
sips -z 32 32 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_32x32.png"
sips -z 64 64 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_32x32@2x.png"
sips -z 128 128 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_128x128.png"
sips -z 256 256 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_128x128@2x.png"
sips -z 256 256 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_256x256.png"
sips -z 512 512 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_256x256@2x.png"
sips -z 512 512 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_512x512.png"
sips -z 1024 1024 src/assets/icon.png --out "$ICONSET_DIR/icon.iconset/icon_512x512@2x.png"
iconutil -c icns "$ICONSET_DIR/icon.iconset" -o src/assets/icon.icns

uv run pyinstaller \
    --windowed \
    --name "MonoBrowser" \
    --paths src \
    --icon src/assets/icon.icns \
    --hidden-import PyQt6.QtWebEngineCore \
    --hidden-import PyQt6.QtWebEngineQuick \
    --hidden-import PyQt6.QtWebChannel \
    --add-data "src/assets/icon.icns:." \
    --add-data "src/assets/icon.png:." \
    --add-data "src/assets/lock:lock" \
    --add-data "src/assets/nav:nav" \
    --add-data "src/assets/tabs:tabs" \
    --add-data "src/assets/menu:menu" \
    --add-data "src/assets/pip:pip" \
    --add-data "pyproject.toml:." \
    --add-data "src/monobrowser/qml:qml" \
    --add-data "src/monobrowser/about-pages:about-pages" \
    src/monobrowser/main.py

FW="dist/MonoBrowser.app/Contents/Frameworks/PyQt6/Qt6/lib/QtWebEngineCore.framework/Versions"

if [ -d "$FW/Resources/Helpers" ] && [ ! -d "$FW/A/Helpers" ]; then
    cp -R "$FW/Resources/Helpers" "$FW/A/Helpers"
fi

if [ -d "$FW/Resources/Resources" ]; then
    cp -R "$FW/Resources/Resources/" "$FW/A/Resources/"
fi

EXE="dist/MonoBrowser.app/Contents/MacOS/MonoBrowser"
vtool -set-build-version macos 11.0 27.0 -replace -output "$EXE" "$EXE"
codesign --force --deep --sign - --timestamp=none dist/MonoBrowser.app

echo "Build complete: dist/MonoBrowser.app"
