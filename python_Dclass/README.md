# LinguaFlow — Smart Multi-Language Translator

A modern desktop translation app built with Python and CustomTkinter. Supports **45+ languages** with dual backends: the free MyMemory API and the professional Baidu Translate API.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Dual Backend** — Free MyMemory (no API key) or Baidu Translate (higher accuracy, requires credentials)
- **45+ Languages** — English, Chinese, Japanese, Korean, French, German, Spanish, and more
- **Clean GUI** — Dark/light theme with dual-panel layout via CustomTkinter
- **Async Translation** — Non-blocking UI using worker threads
- **Text-to-Speech** — Listen to the translated text via Windows SAPI
- **Shortcuts** — `Ctrl+Enter` to translate, `Ctrl+Shift+C` to copy, `Ctrl+A` to select all
- **Swap Languages** — One-click swap between source and target languages
- **Persistent Settings** — Backend choice and API credentials saved locally

## Screenshot

```
┌─────────────────────────────────────────────────────────┐
│                   🌐  LinguaFlow                        │
│              Smart Multi-Language Translator             │
├────────────────────┬────────────────────────────────────┤
│   FROM: English ▼  │        TO: Chinese (Simplified) ▼  │
│   [ ⇄ swap ]       │                                    │
├────────────────────┼────────────────────────────────────┤
│                    │                                    │
│   Original text    │   Translated text                  │
│   input area       │   output area                      │
│                    │                                    │
│                    │                                    │
├────────────────────┴────────────────────────────────────┤
│  [ 🔊 Speak ]  [ 📋 Copy ]  [ 🔄 Pasted text ]         │
│                    [ 🌍 Translate ]                      │
│  Status: Ready                                          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12 or newer
- Windows 10 / 11

### Install

```bash
git clone https://github.com/jack-Li050306/python
cd LinguaFlow
pip install -r requirements.txt
```

### Run

```bash
python translator.py
```

Select your source and target languages, type (or paste) text, and click **Translate** — or press `Ctrl+Enter`.

### Using Baidu Translate

1. Click **Settings** in the bottom-left corner
2. Switch the backend to **Baidu**
3. Enter your Baidu Translate API App ID and Secret Key ([apply here](https://fanyi-api.baidu.com/))
4. The app uses Baidu for all subsequent translations until you switch back

MyMemory needs no configuration and works out of the box.

## Project Structure

```
python_Dclass/
├── translator.py              # Main application (GUI + translation engine)
├── requirements.txt           # Python dependencies
├── .gitignore
├── README.md
├── ppt/
│   ├── build_pptx.py          # Script to auto-generate the project PPTX
│   ├── index.html             # Magazine-style horizontal HTML slide deck
│   └── assets/
│       └── motion.min.js      # Animation library for HTML slides
└── 报告/
    └── 翻译器设计报告.doc       # Design report (Chinese)
```

## Architecture

```
┌──────────────┐     ┌─────────────────┐
│   LinguaFlow │────▶│    Backend      │  (ABC)
│   GUI Layer  │     ├─────────────────┤
│  (CustomTk)  │     │ MyMemoryBackend │  Free, no API key
│              │     │ BaiduBackend    │  MD5-signed auth
└──────────────┘     └─────────────────┘
        │                      │
        ▼                      ▼
  translator_config.json   HTTP APIs
  (persistent settings)    (mymemory / baidu)
```

- **Strategy Pattern** — `Backend` abstract base class with `MyMemoryBackend` and `BaiduBackend` implementations
- **Worker Threads** — Translation runs on daemon threads; callbacks update the UI on the main thread
- **Config Hot-Reload** — Backend and credentials load from `translator_config.json` on every translation

## Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern themed Tkinter widgets |
| `requests` | HTTP calls to translation APIs |
| `python-pptx` | PPTX generation (`ppt/build_pptx.py` only) |

All other dependencies are Python standard library modules.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgements

- [MyMemory](https://mymemory.translated.net/) — Free translation API
- [Baidu Translate](https://fanyi-api.baidu.com/) — Professional translation API
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern Tkinter theming
