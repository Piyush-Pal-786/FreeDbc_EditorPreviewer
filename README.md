# FreeDBC Editor & Previewer

> A **cross-platform, portable, open-source** DBC (CAN Database) file viewer  
> and editor with Excel/CSV export — built with Python + CustomTkinter.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## ✨ Features

| Feature | Detail |
|---|---|
| 📂 **Import DBC** | Load any standard `.dbc` file |
| 👀 **Preview** | Browse messages & signals in a clean split-panel view |
| ✏️ **Edit** | Modify signal/message names, units, factors, offsets, comments by double-clicking |
| 💾 **Save DBC** | Write changes back to a valid `.dbc` file |
| 📊 **Export Excel** | Multi-sheet `.xlsx` workbook (summary + per-message sheets) |
| 📄 **Export CSV** | Flat `.csv` for any spreadsheet tool |
| 🔍 **Search** | Filter messages by name or ID instantly |
| ⌨️ **Shortcuts** | `Ctrl+O` Import · `Ctrl+S` Save · `Ctrl+E` Excel |

---

## 🖥️ Screenshot

```
┌──────────────────────────────────────────────────────────────────────┐
│  🔌 FreeDBC  Editor & Previewer   [Import] [Save] [Excel] [CSV] [?] │
├────────────────────┬─────────────────────────────────────────────────┤
│  📋 Messages       │  ⚡ Signals — EngineData          [✏️ Edit]    │
│  ─────────────     │  ──────────────────────────────────────────────│
│  0x064 EngineData  │  EngineSpeed  | 0 | 16 | LE | 0.25 | …        │
│  0x0C8 VehicleSpd  │  EngineTemp   | 16| 8  | LE | 0.5  | …        │
│  0x12C BrakeData   │  ThrottlePos  | 24| 8  | LE | 0.4  | …        │
└────────────────────┴─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.9+** — [python.org](https://python.org)
- Tkinter (bundled with Python on Windows/macOS; on Linux: `sudo apt install python3-tk`)

### 2. Clone & install

```bash
git clone https://github.com/your-org/FreeDbc_EditorPreviewer.git
cd FreeDbc_EditorPreviewer
pip install -r requirements.txt
```

### 3. Run

```bash
python src/main.py
```

A sample DBC file is provided in `sample_dbc/sample.dbc` to try immediately.

---

## 📦 Build a Single Portable Executable

No Python installation required on the target machine.

```bash
pip install pyinstaller
pyinstaller build.spec
```

The output is a **single self-contained file** in `dist/`:

| Platform | File |
|---|---|
| Windows | `dist/FreeDBC_EditorPreviewer.exe` |
| macOS   | `dist/FreeDBC_EditorPreviewer` |
| Linux   | `dist/FreeDBC_EditorPreviewer` |

> **Tip:** GitHub Actions (`.github/workflows/build.yml`) builds all three  
> automatically on every tagged release.

---

## 🗂️ Project Structure

```
FreeDbc_EditorPreviewer/
├── src/
│   ├── main.py                  # Entry point
│   ├── core/
│   │   ├── dbc_parser.py        # DBC loading, editing, saving (cantools)
│   │   └── excel_exporter.py    # XLSX & CSV export (openpyxl)
│   └── ui/
│       ├── app_window.py        # Main window (CustomTkinter + ttk)
│       └── edit_dialog.py       # Signal / message edit dialogs
├── sample_dbc/
│   └── sample.dbc               # Example DBC file
├── app_ideas/
│   └── DBC_EditorPreviewer.textproto   # Original design spec
├── .github/workflows/build.yml  # CI/CD — build on all 3 platforms
├── requirements.txt
├── build.spec                   # PyInstaller configuration
└── README.md
```

---

## 🛠️ Technology Stack

| Component | Library | Why |
|---|---|---|
| GUI framework | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Modern dark/light UI, pure Python, cross-platform |
| Data tables | tkinter `ttk.Treeview` | Fast, native scrolling, no extra deps |
| DBC parsing | [cantools](https://github.com/eerimoq/cantools) | Industry-standard, handles complex DBC |
| Excel export | [openpyxl](https://openpyxl.readthedocs.io) | Full XLSX support with styles |
| Packaging | [PyInstaller](https://pyinstaller.org) | Single-file, no-install executable |

---

## 🤝 Contributing

Contributions are welcome!

1. **Fork** the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push and open a **Pull Request**

Please follow the existing code style and add a brief description to your PR.

### Reporting issues

Use GitHub Issues — include your OS, Python version, and the error message.

---

## 📄 License

MIT © 2026 — see [LICENSE](LICENSE) for details.
