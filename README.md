# MonoBrowser

<img src="icon.png" alt="MonoBrowser logo" width="64" height="64">

Minimal browser built with **PyQt6** + **QtWebEngine**.

## Structure

```
monobrowser/
├── main.py         ← entry point
├── browser.py      ← SimpleBrowser (UI, tabs, navigation)
├── pages.py        ← internal page rendering
├── tab_page.py     ← TabPage widget
├── utils.py        ← helpers, constants
├── pages/
│   ├── version.html
│   ├── newtab.html
│   └── settings.html
├── build.sh        ← PyInstaller build script
└── pyproject.toml
```

## Internal pages

| URL              | Description  |
| ---------------- | ------------ |
| `about:version`  | Version info |
| `about:newtab`   | New tab page |
| `about:settings` | Settings     |

## Development

```bash
uv run main.py
```

## Build (standalone .app)

```bash
./build.sh
```

Output: `dist/MonoBrowser.app`

```bash
open dist/MonoBrowser.app
```
