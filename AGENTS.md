# AGENTS.md

Tiny PyQt6 + QtWebEngine browser.

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
- Tests cover only `utils.py` (headless-safe: no `QApplication`). GUI code (`browser.py`, `tab_page.py`) needs a display — don't add widget tests.

## CI

- Release workflow `.github/workflows/release.yml` on tag `v*` (macos-14 arm64): verify → `./build.sh` → `ditto` zip → GitHub Release with zip asset. Build is unsigned (Gatekeeper warning applies).

## Code map

- Entrypoint `src/monobrowser/main.py` (`-m monobrowser.main`) → `SimpleBrowser` in `src/monobrowser/browser.py` (tabs via `QTabBar` + `QStackedWidget`, URL/search dispatch in `navigate_to_url`).
- `src/monobrowser/tab_page.py`: `TabPage` = thin `QWebEngineView` wrapper. Every `TabPage(...)` must pass `new_window_callback=self.create_popup_tab`, otherwise `target=_blank` links from that tab die silently (`BrowserPage.createWindow` needs the factory).- `src/monobrowser/utils.py`: URL heuristics (`is_likely_url`, `build_url`), version from `pyproject.toml`, bundled-vs-dev asset paths.
- `src/monobrowser/about_pages.py` + `src/monobrowser/about-pages/*.html`: `about:version`, `about:newtab`, `about:settings` rendered via `setHtml`; search-engine switch intercepts `https://monobrowser.internal/set-search?`.

## Gotchas

- Package imports (`from monobrowser.utils import ...`); the package installs editable via `uv sync` (hatchling build-system). PyInstaller uses `--paths src` in `build.sh` — keep it in sync with the imports.
- Dev vs bundled paths: `utils._is_bundled()` switches between `sys._MEIPASS` and source-relative paths; PyInstaller `--add-data` entries in `build.sh` must cover any new asset/about-page.
- `MonoBrowser.spec` and `src/assets/icon.icns` are gitignored build artifacts (`.gitignore`: `*.spec`, `*.icns`); do not commit them. Source icon is `src/assets/icon.png`.
