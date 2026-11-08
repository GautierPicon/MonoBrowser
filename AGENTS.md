# AGENTS.md

Tiny PyQt6 + Qt Quick/QML + QtWebEngine browser (macOS-only; Windows/Linux untested and unsupported — build/CI/release are macOS-only, do not port without explicit request).

## Run / build

- Dev (requires macOS display; will fail headless over SSH): `uv run -m monobrowser.main`
- Always use `uv run` (`uv run pyinstaller ...`); `.python-version` pins `3.11`, `requires-python >=3.11`.
- Build macOS `.app`: `./build.sh` → `open dist/MonoBrowser.app`
  - macOS-only (`sips`, `iconutil`). Destructively wipes `dist/` + `build/`, regenerates `icon.icns`.
  - Ends with manual `QtWebEngineCore.framework` fixup (copies `Helpers`/`Resources` under `Versions/A/`); if the built app shows a blank page, that step broke.

## Verify (order: lint -> typecheck -> test)

- `uv run ruff check .` / `uv run ruff format --check .`
- `uv run mypy src tests`
- `uv run pytest -q` (single file: `uv run pytest tests/test_utils.py -q`)
- QML: `qmllint -I .venv/lib/python3.11/site-packages/PyQt6/Qt6/qml src/monobrowser/qml/Main.qml src/monobrowser/qml/chrome/*.qml src/monobrowser/qml/TabView.qml src/monobrowser/qml/Theme.qml` — the `-I` points at the Qt bundled with PyQt6; without it, `QtQuick` cannot be resolved. One known false positive remains on `Theme.qml` (see Gotchas).
- Tests cover only `utils.py` (headless-safe: no QGuiApplication). QML/GUI code needs a display — don't add GUI tests.

## CI

- Release workflow `.github/workflows/release.yml` on tag `v*` (macos-14 arm64): verify → `./build.sh` → `ditto` zip → GitHub Release with zip asset. Build is unsigned (Gatekeeper warning applies).
- The workflow is only registered once `.github/workflows/` exists on remote `main`; pushing a tag alone never triggers a run. Moving/re-pushing a tag retriggers the build and fails at `gh release create` if the release exists — `gh workflow disable release` first in that case. Never delete a release's tag: GitHub orphans the release into an asset-less draft (`gh release delete --cleanup-tag` also removes the local tag).

## Style

- No comments in code (Python, QML, shell): the code must speak for itself. Only functional directives are allowed, such as `# type: ignore[...]` or `// qmllint disable ...`.

## Code map

- Entrypoint `src/monobrowser/main.py` (`-m monobrowser.main`): `QGuiApplication` + `QQmlApplicationEngine`, loads `src/monobrowser/qml/Main.qml`. `QT_QUICK_CONTROLS_STYLE=Basic` is set there because PyQt6 exposes no `QQuickStyle` binding.
- `src/monobrowser/qml/Main.qml`: `ApplicationWindow` (frameless, custom traffic lights + tab strip + toolbar), owns the tab `ListModel` and one `WebEngineView` per tab (`TabView.qml`), plus all navigation/URL dispatch and shortcuts. `TabView.qml` (web content) and `Theme.qml` (singleton via `qmldir`) stay at the root; the browser-chrome components live in `qml/chrome/` (`TabStrip.qml`, `Toolbar.qml`, `NavButton.qml`, `TrafficLights.qml`, `ResizeGrip.qml`, `AppMenu.qml`), imported from `Main.qml` with `import "chrome"` and using `import ".."` for `Theme`.
- `src/monobrowser/bridge.py`: `Bridge` QObject injected as the `bridge` property of `Main.qml` through `QQmlApplicationEngine.setInitialProperties` (search engine state, `resolveAddress`, `internalAction`/`internalParam`, about-page HTML). `Main.qml` declares `property var bridge: null` so the access is lint-clean. Keep a Python reference to it in `main.py`, otherwise QML sees `null`.
- `src/monobrowser/utils.py`: URL heuristics (`is_likely_url`, `build_url`, `resolve_address_text`), internal-URL parsing (`internal_url_action`), version from `pyproject.toml`, bundled-vs-dev paths (`_resource_path`, `_assets_path`, `qml_path`).
- `src/monobrowser/about_pages.py` + `src/monobrowser/about-pages/*.html`: `version_html()`, `newtab_html()`, `settings_html(engine)` rendered via `WebEngineView.loadHtml`; the search-engine switch goes through `https://monobrowser.internal/set-search?`.

## Gotchas

- The window is **frameless** on purpose: a titled window with `NSFullSizeContentView` leaves a dead ~28px band on top, and Qt Quick has no supported way to fill it. Consequences: no native shadow/rounded corners, no native resize borders — resizing is done by `ResizeGrip.qml` calling `Window.window.startSystemResize` (`startSystemResize` was dropped from the `Window` attached type in Qt 6.12; `QWindow` still has it), dragging by `Window.startSystemMove`.
- Theme follows macOS through `Theme.qml` (`Qt.styleHints.colorScheme`); about-pages use CSS `prefers-color-scheme`. No manual toggle.
- QML diagnostics in VSCode/Codium come from the `qt-qml` extension, which downloads a standalone `qmlls` with no Qt install of its own: `.vscode/settings.json` points `qt-qml.qmlls.additionalImportPaths` at the PyQt6-bundled `Qt6/qml` dir. Without it every QML file drowns in bogus `Failed to import QtQuick` warnings. That qmlls also reports `colorScheme` on `Qt.styleHints` as missing (its `QStyleHints` stub predates Qt 6.5) and types `createObject()` as `QObject` — both are suppressed inline with `// qmllint disable missing-property`. Linting `Theme.qml` standalone always reports "not declared as singleton in qmldir" because the linter ignores the sibling `qmldir`.
- Package imports (`from monobrowser.utils import ...`); the package installs editable via `uv sync` (hatchling build-system). PyInstaller uses `--paths src` in `build.sh` — keep it in sync with the imports.
- Dev vs bundled paths: `utils._is_bundled()` switches between `sys._MEIPASS` and source-relative paths; PyInstaller `--add-data` entries in `build.sh` must cover any new asset/about-page/QML file (`src/monobrowser/qml` is bundled as `qml`).
- `MonoBrowser.spec` and `src/assets/icon.icns` are gitignored build artifacts (`.gitignore`: `*.spec`, `*.icns`); do not commit them. Source icon is `src/assets/icon.png`.
