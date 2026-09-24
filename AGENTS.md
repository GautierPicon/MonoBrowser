# AGENTS.md

Tiny PyQt6 + QtWebEngine browser. No tests, lint, typecheck, or CI.

## Run / build

- Dev (requires macOS display; will fail headless over SSH): `uv run src/monobrowser/main.py`
- Always use `uv run` (`uv run pyinstaller ...`); `.python-version` pins `3.11`, `requires-python >=3.11`.
- Build macOS `.app`: `./build.sh` → `open dist/MonoBrowser.app`
  - macOS-only (`sips`, `iconutil`). Destructively wipes `dist/` + `build/`, regenerates `icon.icns`.
  - Ends with manual `QtWebEngineCore.framework` fixup (copies `Helpers`/`Resources` under `Versions/A/`); if the built app shows a blank page, that step broke.

## Code map

- Entrypoint `src/monobrowser/main.py` → `SimpleBrowser` in `src/monobrowser/browser.py` (tabs via `QTabBar` + `QStackedWidget`, URL/search dispatch in `navigate_to_url`).
- `src/monobrowser/tab_page.py`: `TabPage` = thin `QWebEngineView` wrapper.
- `src/monobrowser/utils.py`: URL heuristics (`is_likely_url`, `build_url`), version from `pyproject.toml`, bundled-vs-dev asset paths.
- `src/monobrowser/about_pages.py` + `src/monobrowser/about-pages/*.html`: `about:version`, `about:newtab`, `about:settings` rendered via `setHtml`; search-engine switch intercepts `https://monobrowser.internal/set-search?`.

## Gotchas

- Flat intra-package imports (`from browser import ...`, not `from monobrowser import ...`): run as script path above. `python -m monobrowser` does not work.
- Dev vs bundled paths: `utils._is_bundled()` switches between `sys._MEIPASS` and source-relative paths; PyInstaller `--add-data` entries in `build.sh` must cover any new asset/about-page.
- `MonoBrowser.spec` and `src/assets/icon.icns` are gitignored build artifacts (`.gitignore`: `*.spec`, `*.icns`); do not commit them. Source icon is `src/assets/icon.png`.
