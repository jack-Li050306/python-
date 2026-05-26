"""
LinguaFlow - Beautiful Multi-Language Translator
Backends: MyMemory (free, default) + Baidu Translate (optional API key)
"""

import json
import hashlib
import random
import platform
import customtkinter as ctk
import requests
import threading
from pathlib import Path

# ── Paths ────────────────────────────────────────────
BASE = Path(__file__).parent
CONFIG = BASE / "translator_config.json"

# ── Theme ────────────────────────────────────────────
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

# ── Display name → internal key ──────────────────────
LANG_KEYS: dict[str, str] = {
    "Auto Detect（自动检测）":       "auto",
    "English（英文）":                "en",
    "Chinese Simplified（简体中文）":  "zh-CN",
    "Chinese Traditional（繁体中文）": "zh-TW",
    "Japanese（日文）":               "ja",
    "Korean（韩文）":                 "ko",
    "French（法文）":                 "fr",
    "German（德文）":                 "de",
    "Spanish（西班牙文）":            "es",
    "Portuguese（葡萄牙文）":         "pt",
    "Italian（意大利文）":            "it",
    "Russian（俄文）":                "ru",
    "Arabic（阿拉伯文）":             "ar",
    "Hindi（印地文）":               "hi",
    "Thai（泰文）":                   "th",
    "Vietnamese（越南文）":          "vi",
    "Dutch（荷兰文）":               "nl",
    "Turkish（土耳其文）":           "tr",
    "Polish（波兰文）":              "pl",
    "Swedish（瑞典文）":             "sv",
    "Danish（丹麦文）":              "da",
    "Finnish（芬兰文）":             "fi",
    "Greek（希腊文）":               "el",
    "Hebrew（希伯来文）":            "he",
    "Indonesian（印尼文）":          "id",
    "Malay（马来文）":               "ms",
    "Bengali（孟加拉文）":           "bn",
    "Ukrainian（乌克兰文）":         "uk",
    "Czech（捷克文）":               "cs",
    "Romanian（罗马尼亚文）":        "ro",
    "Hungarian（匈牙利文）":         "hu",
    "Norwegian（挪威文）":           "no",
    "Slovak（斯洛伐克文）":          "sk",
    "Bulgarian（保加利亚文）":       "bg",
    "Catalan（加泰罗尼亚文）":       "ca",
    "Croatian（克罗地亚文）":        "hr",
    "Serbian（塞尔维亚文）":         "sr",
    "Slovenian（斯洛文尼亚文）":     "sl",
    "Estonian（爱沙尼亚文）":        "et",
    "Latvian（拉脱维亚文）":         "lv",
    "Lithuanian（立陶宛文）":        "lt",
    "Tamil（泰米尔文）":             "ta",
    "Telugu（泰卢固文）":            "te",
    "Urdu（乌尔都文）":              "ur",
    "Persian（波斯文）":             "fa",
    "Filipino（菲律宾文）":          "tl",
    "Swahili（斯瓦希里文）":         "sw",
}

LANG_NAMES = list(LANG_KEYS.keys())
TARGET_LANGS = [k for k in LANG_NAMES if "Auto" not in k]


# ═══════════════════════════════════════════════════════
#  TRANSLATION BACKENDS
# ═══════════════════════════════════════════════════════

class Backend:
    """Abstract translation backend."""
    name: str = ""
    needs_key: bool = False

    def translate(self, text: str, src_key: str, tgt_key: str) -> str:
        raise NotImplementedError


class MyMemoryBackend(Backend):
    """MyMemory — free, no API key, works globally."""
    name = "MyMemory (Free)"
    needs_key = False

    # MyMemory uses ISO codes like Google, 'zh-CN' etc.
    MAP = {
        "auto": "Autodetect",
        "zh-CN": "zh-CN", "zh-TW": "zh-TW",
    }

    BASE = "https://api.mymemory.translated.net/get"

    def translate(self, text: str, src_key: str, tgt_key: str) -> str:
        src = self.MAP.get(src_key, src_key)
        tgt = self.MAP.get(tgt_key, tgt_key)
        if src == "auto":
            src = "Autodetect"
        if tgt == "auto":
            raise ValueError("Target cannot be auto-detect")

        # MyMemory has 500-char limit per request; chunk if needed
        chunks = [text[i:i+400] for i in range(0, len(text), 400)]
        results = []
        for chunk in chunks:
            resp = requests.get(
                self.BASE,
                params={"q": chunk, "langpair": f"{src}|{tgt}"},
                timeout=20,
            )
            data = resp.json()
            status = data.get("responseStatus", 0)
            if status != 200:
                raise RuntimeError(
                    data.get("responseDetails", f"MyMemory error {status}")
                )
            results.append(data["responseData"]["translatedText"])
        return " ".join(results)


class BaiduBackend(Backend):
    """Baidu Translate — requires appid + secret, high accuracy for CN."""
    name = "Baidu Translate"
    needs_key = True

    BAIDU_CODES = {
        "auto": "auto", "en": "en", "zh-CN": "zh", "zh-TW": "cht",
        "ja": "jp", "ko": "kor", "fr": "fra", "de": "de",
        "es": "spa", "pt": "pt", "it": "it", "ru": "ru",
        "ar": "ara", "hi": "hi", "th": "th", "vi": "vie",
        "nl": "nl", "tr": "tr", "pl": "pl", "sv": "swe",
        "da": "dan", "fi": "fin", "el": "el", "id": "id",
        "ms": "msa", "uk": "ukr", "cs": "cs", "ro": "ro",
        "hu": "hu", "no": "nor", "sk": "sk", "bg": "bg",
        "ca": "ca", "hr": "hrv", "sr": "srp", "sl": "sl",
        "et": "est", "lv": "lv", "lt": "lt",
        "tl": "tl", "sw": "sw",
    }
    API = "https://fanyi-api.baidu.com/api/trans/vip/translate"

    def __init__(self, appid: str, secret: str):
        self.appid = appid.strip()
        self.secret = secret.strip()

    def translate(self, text: str, src_key: str, tgt_key: str) -> str:
        src = self.BAIDU_CODES.get(src_key, src_key)
        tgt = self.BAIDU_CODES.get(tgt_key, tgt_key)
        if tgt == "auto":
            raise ValueError("Target cannot be auto-detect")

        salt = str(random.randint(10000, 99999))
        sign_str = self.appid + text + salt + self.secret
        sign = hashlib.md5(sign_str.encode()).hexdigest()

        resp = requests.get(self.API, params={
            "q": text, "from": src, "to": tgt,
            "appid": self.appid, "salt": salt, "sign": sign,
        }, timeout=15)
        data = resp.json()
        if "error_code" in data:
            err = data.get("error_msg", "Baidu API error")
            raise RuntimeError(f"Baidu[{data['error_code']}]: {err}")
        return "\n".join(d["dst"] for d in data.get("trans_result", []))


# ═══════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ═══════════════════════════════════════════════════════

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, config: dict, on_save):
        super().__init__(master)
        self.config = config
        self.on_save = on_save
        self.title("API Settings")
        self.geometry("440x340")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # center on parent
        self.update_idletasks()
        pw, ph = master.winfo_width(), master.winfo_height()
        px, py = master.winfo_x(), master.winfo_y()
        w, h = 440, 340
        self.geometry(f"{w}x{h}+{px+(pw-w)//2}+{py+(ph-h)//2}")

        self._build()

    def _build(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            f, text="Translation Backend",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            f, text="Select the translation engine to use.",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray55"),
        ).pack(anchor="w", pady=(0, 12))

        # Backend selector
        self.backend_var = ctk.StringVar(value=self.config.get("backend", "mymemory"))
        self.mymemory_radio = ctk.CTkRadioButton(
            f, text="MyMemory (Free) — no API key required",
            variable=self.backend_var, value="mymemory",
            font=ctk.CTkFont(size=13), command=self._toggle_keys,
        )
        self.mymemory_radio.pack(anchor="w", pady=4)

        self.baidu_radio = ctk.CTkRadioButton(
            f, text="Baidu Translate — higher accuracy, requires API key",
            variable=self.backend_var, value="baidu",
            font=ctk.CTkFont(size=13), command=self._toggle_keys,
        )
        self.baidu_radio.pack(anchor="w", pady=4)

        # Baidu credentials
        self.keys_frame = ctk.CTkFrame(f, fg_color="transparent")
        self.keys_frame.pack(fill="x", pady=(12, 8))

        ctk.CTkLabel(
            self.keys_frame, text="App ID",
            font=ctk.CTkFont(size=11), text_color=("gray45", "gray55"),
        ).pack(anchor="w")
        self.appid_entry = ctk.CTkEntry(self.keys_frame, height=34, corner_radius=8)
        self.appid_entry.pack(fill="x", pady=(2, 10))
        self.appid_entry.insert(0, self.config.get("baidu_appid", ""))

        ctk.CTkLabel(
            self.keys_frame, text="Secret Key",
            font=ctk.CTkFont(size=11), text_color=("gray45", "gray55"),
        ).pack(anchor="w")
        self.secret_entry = ctk.CTkEntry(self.keys_frame, height=34, corner_radius=8, show="*")
        self.secret_entry.pack(fill="x", pady=(2, 0))
        self.secret_entry.insert(0, self.config.get("baidu_secret", ""))

        # Help link
        ctk.CTkLabel(
            f, text='Get free API key: https://fanyi-api.baidu.com',
            font=ctk.CTkFont(size=10), text_color=("#2980b9", "#85c1e9"),
            cursor="hand2",
        ).pack(anchor="w", pady=(2, 12))

        # Buttons
        btn_frame = ctk.CTkFrame(f, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 0))
        ctk.CTkButton(
            btn_frame, text="Cancel", width=90, height=34, corner_radius=8,
            fg_color="transparent", border_width=1,
            border_color=("gray65", "gray40"),
            text_color=("gray45", "gray55"),
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_frame, text="Save", width=90, height=34, corner_radius=8,
            command=self._save,
        ).pack(side="right")

        self._toggle_keys()

    def _toggle_keys(self):
        use_baidu = self.backend_var.get() == "baidu"
        for child in self.keys_frame.winfo_children():
            try:
                child.configure(state="normal" if use_baidu else "disabled")
            except Exception:
                pass
            # Also handle nested children
            try:
                for sub in child.winfo_children():
                    try:
                        sub.configure(state="normal" if use_baidu else "disabled")
                    except Exception:
                        pass
            except Exception:
                pass

    def _save(self):
        backend = self.backend_var.get()
        self.config["backend"] = backend
        self.config["baidu_appid"] = self.appid_entry.get().strip()
        self.config["baidu_secret"] = self.secret_entry.get().strip()
        with open(CONFIG, "w", encoding="utf-8") as fh:
            json.dump(self.config, fh, indent=2)
        self.on_save()
        self.destroy()


# ═══════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════

class LinguaFlow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LinguaFlow - Smart Translator")
        self.geometry("960x720")
        self.minsize(820, 620)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 960, 720
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._load_config()
        self._build_backend()
        self._build_ui()
        self._bind_shortcuts()

    # ── Config & Backend ────────────────────────────────
    def _load_config(self):
        try:
            if CONFIG.exists():
                self.cfg = json.loads(CONFIG.read_text("utf-8"))
            else:
                self.cfg = {"backend": "mymemory", "baidu_appid": "", "baidu_secret": ""}
        except Exception:
            self.cfg = {"backend": "mymemory", "baidu_appid": "", "baidu_secret": ""}

    def _build_backend(self):
        if self.cfg.get("backend") == "baidu" and self.cfg.get("baidu_appid") and self.cfg.get("baidu_secret"):
            try:
                self.backend = BaiduBackend(self.cfg["baidu_appid"], self.cfg["baidu_secret"])
                return
            except Exception:
                pass
        self.backend = MyMemoryBackend()

    def _reload_backend(self):
        self._load_config()
        self._build_backend()
        name = self.backend.name
        self._set_status(f"Switched to {name}", "green")
        self._update_backend_label()

    def _update_backend_label(self):
        self.backend_label.configure(text=f"  Engine: {self.backend.name}  ")

    # ── UI Construction ───────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew", padx=32, pady=24)
        self.main.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_lang_selector()
        self._build_text_panels()
        self._build_action_bar()
        self._build_status_bar()

    def _build_header(self):
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top, text="LinguaFlow",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=("#1a5276", "#85c1e9"),
        ).pack(side="left")

        # Settings gear button
        self.settings_btn = ctk.CTkButton(
            top, text="Settings", width=74, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            border_color=("gray65", "gray40"),
            text_color=("gray45", "gray55"),
            hover_color=("gray85", "gray28"),
            command=self._open_settings,
        )
        self.settings_btn.pack(side="right")

        subtitle_row = ctk.CTkFrame(frame, fg_color="transparent")
        subtitle_row.pack(fill="x")
        ctk.CTkLabel(
            subtitle_row, text="Seamless translation across 45+ languages",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
        ).pack(side="left")

        self.backend_label = ctk.CTkLabel(
            subtitle_row, text=f"  Engine: {self.backend.name}  ",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray55"),
        )
        self.backend_label.pack(side="right")

    def _build_lang_selector(self):
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(expand=True)

        ctk.CTkLabel(
            inner, text="FROM", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray40", "gray55"),
        ).pack(side="left", padx=(0, 6))

        self.src_combo = ctk.CTkComboBox(
            inner, values=LANG_NAMES, font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13), width=195, height=38,
            corner_radius=10, state="readonly",
        )
        self.src_combo.set("Auto Detect（自动检测）")
        self.src_combo.pack(side="left", padx=4)

        self.swap_btn = ctk.CTkButton(
            inner, text="⇄", width=44, height=38, corner_radius=10,
            font=ctk.CTkFont(size=20),
            fg_color=("gray25", "gray22"),
            hover_color=("#2980b9", "#2471a3"),
            command=self._swap,
        )
        self.swap_btn.pack(side="left", padx=14)

        ctk.CTkLabel(
            inner, text="TO", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray40", "gray55"),
        ).pack(side="left", padx=(14, 6))

        self.tgt_combo = ctk.CTkComboBox(
            inner, values=TARGET_LANGS, font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13), width=195, height=38,
            corner_radius=10, state="readonly",
        )
        self.tgt_combo.set("Chinese Simplified（简体中文）")
        self.tgt_combo.pack(side="left", padx=4)

    def _build_text_panels(self):
        container = ctk.CTkFrame(self.main, fg_color="transparent")
        container.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        container.grid_columnconfigure((0, 1), weight=1, uniform="panel")
        container.grid_rowconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        # --- Input panel ---
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkLabel(
            hdr, text="Input Text", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray55"),
        ).pack(side="left")
        self.char_label = ctk.CTkLabel(
            hdr, text="0 / 5000", font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50"),
        )
        self.char_label.pack(side="right")

        self.input_box = ctk.CTkTextbox(
            left, font=ctk.CTkFont(size=14), corner_radius=12,
            border_width=2, border_color=("gray70", "gray35"),
            fg_color=("gray93", "gray15"), wrap="word",
        )
        self.input_box.grid(row=1, column=0, sticky="nsew")
        self.input_box.bind("<KeyRelease>", self._on_input_change)

        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self._mini_btn(btns, "Clear", self._clear_input).pack(side="left", padx=(0, 5))
        self._mini_btn(btns, "Paste", self._paste).pack(side="left")

        # --- Output panel ---
        right = ctk.CTkFrame(container, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        hdr2 = ctk.CTkFrame(right, fg_color="transparent")
        hdr2.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkLabel(
            hdr2, text="Translation", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray55"),
        ).pack(side="left")

        self.output_box = ctk.CTkTextbox(
            right, font=ctk.CTkFont(size=14), corner_radius=12,
            border_width=2, border_color=("gray70", "gray35"),
            fg_color=("gray93", "gray15"), wrap="word",
        )
        self.output_box.grid(row=1, column=0, sticky="nsew")

        btns2 = ctk.CTkFrame(right, fg_color="transparent")
        btns2.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self._mini_btn(btns2, "Copy", self._copy, hover="#27ae60").pack(side="left", padx=(0, 5))
        self._mini_btn(btns2, "Speak", self._speak).pack(side="left")

    def _build_action_bar(self):
        self.translate_btn = ctk.CTkButton(
            self.main, text="Translate", height=50, corner_radius=12,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#2980b9", "#2471a3"),
            hover_color=("#1f6da0", "#1b5e8a"),
            command=self._translate,
        )
        self.translate_btn.grid(row=3, column=0, sticky="ew", pady=(0, 4))

    def _build_status_bar(self):
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.grid(row=4, column=0, sticky="ew", pady=(4, 0))

        self.progress = ctk.CTkProgressBar(frame, height=4, corner_radius=2, mode="indeterminate")

        self.status_dot = ctk.CTkLabel(frame, text="●", font=ctk.CTkFont(size=8), text_color="#27ae60")
        self.status_dot.pack(side="left", padx=(0, 4))

        self.status_label = ctk.CTkLabel(
            frame, text="Ready", font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50"),
        )
        self.status_label.pack(side="left")

    # ── Helpers ────────────────────────────────────────
    @staticmethod
    def _mini_btn(parent, text, cmd, hover="#2980b9"):
        return ctk.CTkButton(
            parent, text=text, width=64, height=28, corner_radius=7,
            font=ctk.CTkFont(size=11), fg_color="transparent",
            border_width=1, border_color=("gray65", "gray38"),
            text_color=("gray45", "gray50"), hover_color=hover, command=cmd,
        )

    def _bind_shortcuts(self):
        self.input_box.bind("<Control-Return>", lambda _: self._translate())
        self.input_box.bind("<Control-a>", self._select_all)
        self.bind_all("<Control-Shift-C>", lambda _: self._copy())

    def _select_all(self, event=None):
        self.input_box.tag_add("sel", "0.0", "end")
        return "break"

    def _set_status(self, msg: str, color: str = "gray"):
        colors = {"green": "#27ae60", "red": "#e74c3c", "yellow": "#f39c12", "gray": "gray50"}
        self.status_dot.configure(text_color=colors.get(color, "gray50"))
        self.status_label.configure(text=msg)

    def _on_input_change(self, event=None):
        text = self.input_box.get("0.0", "end-1c")
        n = len(text)
        self.char_label.configure(text=f"{n} / 5000")
        if n > 4800:
            self.char_label.configure(text_color="#e74c3c")
        elif n > 3500:
            self.char_label.configure(text_color="#f39c12")
        else:
            self.char_label.configure(text_color=("gray50", "gray50"))

    def _open_settings(self):
        SettingsDialog(self, self.cfg, self._reload_backend)

    # ── Actions ────────────────────────────────────────
    def _clear_input(self):
        self.input_box.delete("0.0", "end")
        self.output_box.delete("0.0", "end")
        self._on_input_change()
        self._set_status("Cleared", "green")

    def _paste(self):
        try:
            text = self.clipboard_get()
            self.input_box.delete("0.0", "end")
            self.input_box.insert("0.0", text)
            self._on_input_change()
            self._set_status("Pasted from clipboard", "green")
        except Exception:
            self._set_status("Clipboard is empty", "yellow")

    def _copy(self):
        text = self.output_box.get("0.0", "end-1c").strip()
        if not text:
            self._set_status("Nothing to copy", "yellow")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status("Copied to clipboard!", "green")

    def _speak(self):
        text = self.output_box.get("0.0", "end-1c").strip()
        if not text:
            self._set_status("Nothing to speak", "yellow")
            return
        try:
            import subprocess
            ps_script = f'''
            Add-Type -AssemblyName System.Speech
            $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $s.Speak('{text.replace("'", "''")}')
            '''
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_script],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._set_status("Speaking...", "green")
        except Exception:
            self._set_status("TTS not available", "yellow")

    def _swap(self):
        src = self.src_combo.get()
        tgt = self.tgt_combo.get()
        if "Auto" in src:
            self._set_status("Cannot swap Auto Detect as source — pick a language first", "yellow")
            return

        inp = self.input_box.get("0.0", "end-1c")
        out = self.output_box.get("0.0", "end-1c")
        self.input_box.delete("0.0", "end")
        self.output_box.delete("0.0", "end")
        if out:
            self.input_box.insert("0.0", out)
        if inp:
            self.output_box.insert("0.0", inp)

        self.src_combo.set(tgt)
        self.tgt_combo.set(src)
        self._on_input_change()
        self._set_status("Languages swapped", "green")

    # ── Translation Engine ─────────────────────────────
    def _translate(self):
        text = self.input_box.get("0.0", "end-1c").strip()
        if not text:
            self._set_status("Please enter text to translate", "yellow")
            return

        src_key = LANG_KEYS[self.src_combo.get()]
        tgt_key = LANG_KEYS[self.tgt_combo.get()]

        if src_key == tgt_key and src_key != "auto":
            self._set_status("Source and target are the same language", "yellow")
            return

        self._set_translating(True)
        threading.Thread(
            target=self._run_translation,
            args=(text, src_key, tgt_key),
            daemon=True,
        ).start()

    def _run_translation(self, text: str, src: str, tgt: str):
        try:
            result = self.backend.translate(text, src, tgt)
            self.after(0, self._on_done, result)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _set_translating(self, active: bool):
        if active:
            self.progress.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.progress.start()
            self.translate_btn.configure(state="disabled", text="Translating…")
            self._set_status("Translating…", "yellow")
        else:
            self.progress.stop()
            self.progress.pack_forget()
            self.translate_btn.configure(state="normal", text="Translate")

    def _on_done(self, result: str):
        self._set_translating(False)
        self.output_box.delete("0.0", "end")
        self.output_box.insert("0.0", result)
        self._set_status("Translation complete!", "green")

    def _on_error(self, msg: str):
        self._set_translating(False)
        lo = msg.lower()
        if "block" in lo or "429" in lo:
            msg = "Rate limited — wait a moment and retry"
        elif "connect" in lo or "timeout" in lo or "network" in lo:
            msg = "Network error — check your internet connection"
        elif "baidu[54003" in lo or "baidu[54004" in lo:
            msg = "Baidu quota exhausted — check your account balance"
        elif "baidu[52001" in lo or "baidu[52002" in lo:
            msg = "Baidu auth failed — check App ID and Secret Key in Settings"
        self._set_status(f"Error: {msg[:120]}", "red")


# ── Entry Point ─────────────────────────────────────────
def main():
    app = LinguaFlow()
    app.mainloop()


if __name__ == "__main__":
    main()
