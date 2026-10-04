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
- Tests cover only `utils.py` (headless-safe: no QGuiApplication). QML/GUI code needs a display — don't add GUI tests.

## CI

- Release workflow `.github/workflows/release.yml` on tag `v*` (macos-14 arm64): verify → `./build.sh` → `ditto` zip → GitHub Release with zip asset. Build is unsigned (Gatekeeper warning applies).
- The workflow is only registered once `.github/workflows/` exists on remote `main`; pushing a tag alone never triggers a run. Moving/re-pushing a tag retriggers the build and fails at `gh release create` if the release exists — `gh workflow disable release` first in that case. Never delete a release's tag: GitHub orphans the release into an asset-less draft (`gh release delete --cleanup-tag` also removes the local tag).

## Code map

- Entrypoint `src/monobrowser/main.py` (`-m monobrowser.main`): `QGuiApplication` + `QQmlApplicationEngine`, loads `src/monobrowser/qml/Main.qml`. `QT_QUICK_CONTROLS_STYLE=Basic` is set there because PyQt6 exposes no `QQuickStyle` binding.
- `src/monobrowser/qml/Main.qml`: `ApplicationWindow` (frameless, custom traffic lights + tab strip + toolbar), owns the tab `ListModel` and one `WebEngineView` per tab (`TabView.qml`), plus all navigation/URL dispatch and shortcuts. Other QML files: `TabStrip.qml`, `Toolbar.qml`, `NavButton.qml`, `TrafficLights.qml`, `ResizeGrip.qml`, `Theme.qml` (singleton via `qmldir`), `TabView.qml`.
- `src/monobrowser/bridge.py`: `Bridge` QObject exposed as the `bridge` context property (search engine state, `resolveAddress`, `internalAction`/`internalParam`, about-page HTML). Keep a Python reference to it in `main.py`, otherwise QML sees `null`.
- `src/monobrowser/utils.py`: URL heuristics (`is_likely_url`, `build_url`, `resolve_address_text`), internal-URL parsing (`internal_url_action`), version from `pyproject.toml`, bundled-vs-dev paths (`_resource_path`, `_assets_path`, `qml_path`).
- `src/monobrowser/about_pages.py` + `src/monobrowser/about-pages/*.html`: `version_html()`, `newtab_html()`, `settings_html(engine)` rendered via `WebEngineView.loadHtml`; the search-engine switch goes through `https://monobrowser.internal/set-search?`.

## Gotchas

- The window is **frameless** on purpose: a titled window with `NSFullSizeContentView` leaves a dead ~28px band on top, and Qt Quick has no supported way to fill it. Consequences: no native shadow/rounded corners, no native resize borders — resizing is done by `ResizeGrip.qml` calling `Window.startSystemResize`, dragging by `Window.startSystemMove`.
- Theme follows macOS through `Theme.qml` (`Qt.styleHints.colorScheme`); about-pages use CSS `prefers-color-scheme`. No manual toggle.
- Package imports (`from monobrowser.utils import ...`); the package installs editable via `uv sync` (hatchling build-system). PyInstaller uses `--paths src` in `build.sh` — keep it in sync with the imports.
- Dev vs bundled paths: `utils._is_bundled()` switches between `sys._MEIPASS` and source-relative paths; PyInstaller `--add-data` entries in `build.sh` must cover any new asset/about-page/QML file (`src/monobrowser/qml` is bundled as `qml`).
- `MonoBrowser.spec` and `src/assets/icon.icns` are gitignored build artifacts (`.gitignore`: `*.spec`, `*.icns`); do not commit them. Source icon is `src/assets/icon.png`.
