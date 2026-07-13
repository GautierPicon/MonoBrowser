#!/usr/bin/env bash
set -euo pipefail

rm -rf dist build

mkdir -p src/assets/icon.iconset
sips -z 16 16 src/assets/icon.png --out src/assets/icon.iconset/icon_16x16.png &>/dev/null
sips -z 32 32 src/assets/icon.png --out src/assets/icon.iconset/icon_16x16@2x.png &>/dev/null
sips -z 32 32 src/assets/icon.png --out src/assets/icon.iconset/icon_32x32.png &>/dev/null
sips -z 64 64 src/assets/icon.png --out src/assets/icon.iconset/icon_32x32@2x.png &>/dev/null
sips -z 128 128 src/assets/icon.png --out src/assets/icon.iconset/icon_128x128.png &>/dev/null
sips -z 256 256 src/assets/icon.png --out src/assets/icon.iconset/icon_128x128@2x.png &>/dev/null
sips -z 256 256 src/assets/icon.png --out src/assets/icon.iconset/icon_256x256.png &>/dev/null
sips -z 512 512 src/assets/icon.png --out src/assets/icon.iconset/icon_256x256@2x.png &>/dev/null
sips -z 512 512 src/assets/icon.png --out src/assets/icon.iconset/icon_512x512.png &>/dev/null
sips -z 1024 1024 src/assets/icon.png --out src/assets/icon.iconset/icon_512x512@2x.png &>/dev/null
iconutil -c icns src/assets/icon.iconset
rm -rf src/assets/icon.iconset

uv run pyinstaller \
    --windowed \
    --name "MonoBrowser" \
    --paths src/monobrowser \
    --icon src/assets/icon.icns \
    --add-data "src/assets/icon.icns:." \
    --add-data "src/assets/icon.png:." \
    --add-data "pyproject.toml:." \
    --add-data "src/monobrowser/about-pages:about-pages" \
    src/monobrowser/main.py

FW="dist/MonoBrowser.app/Contents/Frameworks/PyQt6/Qt6/lib/QtWebEngineCore.framework/Versions"

if [ -d "$FW/Resources/Helpers" ] && [ ! -d "$FW/A/Helpers" ]; then
    cp -R "$FW/Resources/Helpers" "$FW/A/Helpers"
fi

if [ -d "$FW/Resources/Resources" ]; then
    cp -R "$FW/Resources/Resources/" "$FW/A/Resources/"
fi

echo "Build complete: dist/MonoBrowser.app"
