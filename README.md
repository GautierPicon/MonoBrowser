# MonoBrowser

<img src="src/assets/icon.png" alt="MonoBrowser logo" width="64" height="64">

Minimal browser built with **PyQt6** + **Qt Quick/QML** + **QtWebEngine**.

> macOS only — Windows and Linux are neither tested nor supported.

## Requirements

- macOS on Apple Silicon
- For development: `uv` and a display

## Development

```bash
uv run -m monobrowser.main
```

## Dependencies

- `src/assets/adblock/hosts.txt` — [StevenBlack/hosts](https://github.com/StevenBlack/hosts) (MIT), unified hosts list (adware + malware, 76 104 unique domains as of November 2026). Used for native ad blocking through a QtWebEngine URL request interceptor, no extensions involved. Settings → Ad blocking toggles the network blocker and an optional CSS-based hiding of ad containers. To refresh it:

  ```bash
  curl -fsSL https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts -o src/assets/adblock/hosts.txt
  ```

## Tests

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest -q
```
## Build (standalone .app)

```bash
./build.sh
```

Output: `dist/MonoBrowser.app`

```bash
open dist/MonoBrowser.app
```
