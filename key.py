"""
Key Sound Mapper
================
특정 키를 누르면 지정한 소리가 나는 글로벌 키→사운드 매핑 앱.
트레이 아이콘으로 백그라운드 실행 지원.

의존성: pip install customtkinter pynput pygame-ce pystray pillow
"""

import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import customtkinter as ctk
import pygame
from pynput import keyboard as kb
from PIL import Image, ImageDraw
import pystray


# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".key_sound_mapper.json"

SPECIAL_KEY_NAMES = {
    kb.Key.space: "Space",
    kb.Key.enter: "Enter",
    kb.Key.tab: "Tab",
    kb.Key.backspace: "Backspace",
    kb.Key.delete: "Delete",
    kb.Key.esc: "Esc",
    kb.Key.up: "↑",
    kb.Key.down: "↓",
    kb.Key.left: "←",
    kb.Key.right: "→",
    kb.Key.shift: "Shift",
    kb.Key.shift_r: "Right Shift",
    kb.Key.ctrl: "Ctrl",
    kb.Key.ctrl_r: "Right Ctrl",
    kb.Key.alt: "Alt",
    kb.Key.alt_r: "Right Alt",
    kb.Key.cmd: "Win",
    kb.Key.cmd_r: "Right Win",
    kb.Key.caps_lock: "Caps Lock",
    kb.Key.insert: "Insert",
    kb.Key.home: "Home",
    kb.Key.end: "End",
    kb.Key.page_up: "PgUp",
    kb.Key.page_down: "PgDn",
    kb.Key.print_screen: "PrtSc",
    kb.Key.scroll_lock: "Scroll Lock",
    kb.Key.pause: "Pause",
    kb.Key.menu: "Menu",
    kb.Key.f1: "F1",
    kb.Key.f2: "F2",
    kb.Key.f3: "F3",
    kb.Key.f4: "F4",
    kb.Key.f5: "F5",
    kb.Key.f6: "F6",
    kb.Key.f7: "F7",
    kb.Key.f8: "F8",
    kb.Key.f9: "F9",
    kb.Key.f10: "F10",
    kb.Key.f11: "F11",
    kb.Key.f12: "F12",
}

KEY_NAME_ALIASES = {
    "space": "Space",
    "enter": "Enter",
    "tab": "Tab",
    "backspace": "Backspace",
    "delete": "Delete",
    "esc": "Esc",
    "up": "↑",
    "down": "↓",
    "left": "←",
    "right": "→",
    "shift": "Shift",
    "shift_r": "Right Shift",
    "ctrl": "Ctrl",
    "ctrl_r": "Right Ctrl",
    "alt": "Alt",
    "alt_r": "Right Alt",
    "cmd": "Win",
    "cmd_r": "Right Win",
    "caps_lock": "Caps Lock",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "page_up": "PgUp",
    "page_down": "PgDn",
    "print_screen": "PrtSc",
    "scroll_lock": "Scroll Lock",
    "pause": "Pause",
    "menu": "Menu",
}

KEYBOARD_LAYOUT = [
    [
        ("Esc", "Esc"),
        ("F1", "F1"), ("F2", "F2"), ("F3", "F3"), ("F4", "F4"),
        ("F5", "F5"), ("F6", "F6"), ("F7", "F7"), ("F8", "F8"),
        ("F9", "F9"), ("F10", "F10"), ("F11", "F11"), ("F12", "F12"),
    ],
    [
        ("`", "`"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"),
        ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"),
        ("0", "0"), ("-", "-"), ("=", "="), ("Backspace", "Backspace"),
    ],
    [
        ("Tab", "Tab"), ("Q", "q"), ("W", "w"), ("E", "e"), ("R", "r"),
        ("T", "t"), ("Y", "y"), ("U", "u"), ("I", "i"), ("O", "o"),
        ("P", "p"), ("[", "["), ("]", "]"), ("\\", "\\"),
    ],
    [
        ("Caps Lock", "Caps Lock"), ("A", "a"), ("S", "s"), ("D", "d"),
        ("F", "f"), ("G", "g"), ("H", "h"), ("J", "j"), ("K", "k"),
        ("L", "l"), (";", ";"), ("'", "'"), ("Enter", "Enter"),
    ],
    [
        ("Shift", "Shift"), ("Z", "z"), ("X", "x"), ("C", "c"),
        ("V", "v"), ("B", "b"), ("N", "n"), ("M", "m"), (",", ","),
        (".", "."), ("/", "/"), ("Right Shift", "Right Shift"),
    ],
    [
        ("Ctrl", "Ctrl"), ("Win", "Win"), ("Alt", "Alt"),
        ("Space", "Space"), ("Right Alt", "Right Alt"),
        ("Right Win", "Right Win"), ("Menu", "Menu"),
        ("Right Ctrl", "Right Ctrl"), ("←", "←"), ("↓", "↓"),
        ("↑", "↑"), ("→", "→"),
    ],
]

KEY_BUTTON_WIDTHS = {
    "Backspace": 120,
    "Tab": 70,
    "Caps Lock": 100,
    "Enter": 90,
    "Shift": 105,
    "Right Shift": 130,
    "Ctrl": 70,
    "Right Ctrl": 95,
    "Alt": 70,
    "Right Alt": 95,
    "Win": 70,
    "Right Win": 95,
    "Space": 220,
    "Menu": 80,
}

KEY_SORT_INDEX = {
    key_str: index
    for index, key_str in enumerate(
        key_str for row in KEYBOARD_LAYOUT for _, key_str in row
    )
}


def normalize_key_str(key_str: str) -> str:
    value = str(key_str).strip()
    if not value:
        return value
    if len(value) == 1 and value.isalpha():
        return value.lower()

    lowered = value.lower()
    if lowered in KEY_NAME_ALIASES:
        return KEY_NAME_ALIASES[lowered]
    if lowered.startswith("f") and lowered[1:].isdigit():
        return lowered.upper()
    return value


def display_key_name(key_str: str) -> str:
    value = normalize_key_str(key_str)
    if len(value) == 1 and value.isalpha():
        return value.upper()
    return value


def key_to_str(key) -> str:
    if hasattr(key, "char") and key.char:
        return normalize_key_str(key.char)
    return normalize_key_str(SPECIAL_KEY_NAMES.get(key, str(key).replace("Key.", "")))


def format_key_list(key_names: list[str]) -> str:
    return ", ".join(display_key_name(key) for key in key_names)


def sort_keys(key_names: list[str]) -> list[str]:
    return sorted(
        key_names,
        key=lambda key: (KEY_SORT_INDEX.get(key, 10_000), display_key_name(key)),
    )


def key_button_width(label: str) -> int:
    if label in KEY_BUTTON_WIDTHS:
        return KEY_BUTTON_WIDTHS[label]
    if len(label) == 1:
        return 48
    return 58


# ─────────────────────────────────────────────
# 트레이 아이콘 이미지 생성
# ─────────────────────────────────────────────
def make_tray_icon(active: bool) -> Image.Image:
    """활성/비활성 상태에 따라 트레이 아이콘 이미지 생성."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = "#a6e3a1" if active else "#f38ba8"
    draw.ellipse([4, 4, size - 4, size - 4], fill=color)
    key_w, key_h = 8, 28
    starts = [10, 20, 30, 40, 50]
    for x in starts:
        draw.rectangle([x, 20, x + key_w - 2, 20 + key_h], fill="white")
    return img


# ─────────────────────────────────────────────
# 사운드 엔진
# ─────────────────────────────────────────────
class SoundEngine:
    def __init__(self) -> None:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        self._cache: dict[str, pygame.mixer.Sound] = {}

    def load(self, path: str) -> bool:
        try:
            self._cache[path] = pygame.mixer.Sound(path)
            return True
        except Exception:
            return False

    def play(self, path: str) -> None:
        if path not in self._cache:
            if not self.load(path):
                return
        self._cache[path].play()

    def unload(self, path: str) -> None:
        self._cache.pop(path, None)

    def quit(self) -> None:
        pygame.mixer.quit()


# ─────────────────────────────────────────────
# 키 리스너
# ─────────────────────────────────────────────
class GlobalKeyListener:
    def __init__(self, on_press_cb) -> None:
        self._callback = on_press_cb
        self._listener: kb.Listener | None = None
        self.active = True

    def _on_press(self, key) -> None:
        if self.active:
            self._callback(key)

    def start(self) -> None:
        self._listener = kb.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()


# ─────────────────────────────────────────────
# 매핑 저장소
# ─────────────────────────────────────────────
class MappingStore:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self.load()

    def all(self) -> dict[str, str]:
        return dict(self._data)

    def add(self, key_str: str, sound_path: str) -> None:
        self._data[normalize_key_str(key_str)] = sound_path
        self.save()

    def add_many(self, key_names: list[str], sound_path: str) -> None:
        for key_str in key_names:
            self._data[normalize_key_str(key_str)] = sound_path
        self.save()

    def remove(self, key_str: str) -> None:
        self._data.pop(normalize_key_str(key_str), None)
        self.save()

    def get_sound(self, key_str: str) -> str | None:
        return self._data.get(normalize_key_str(key_str))

    def has_sound_path(self, sound_path: str) -> bool:
        return sound_path in self._data.values()

    def save(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load(self) -> None:
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                loaded = json.load(f)
        except (OSError, json.JSONDecodeError):
            self._data = {}
            return

        if not isinstance(loaded, dict):
            self._data = {}
            return

        self._data = {
            normalize_key_str(str(key)): str(path)
            for key, path in loaded.items()
        }


# ─────────────────────────────────────────────
# GUI — 매핑 행 위젯
# ─────────────────────────────────────────────
class MappingRow(ctk.CTkFrame):
    def __init__(self, parent, key_str: str, sound_path: str,
                 on_delete, on_test, **kwargs) -> None:
        super().__init__(parent, fg_color="#1e1e2e", corner_radius=10, **kwargs)

        ctk.CTkLabel(
            self,
            text=display_key_name(key_str),
            width=96,
            height=34,
            font=ctk.CTkFont(family="Courier New", size=15, weight="bold"),
            fg_color="#313244",
            text_color="#cdd6f4",
            corner_radius=8
        ).pack(side="left", padx=(12, 8), pady=8)

        ctk.CTkLabel(
            self,
            text=Path(sound_path).name,
            font=ctk.CTkFont(size=13),
            text_color="#a6adc8",
            anchor="w"
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            self,
            text="▶",
            width=36,
            height=28,
            fg_color="#45475a",
            hover_color="#585b70",
            text_color="#a6e3a1",
            font=ctk.CTkFont(size=13),
            command=lambda: on_test(sound_path)
        ).pack(side="right", padx=(0, 8), pady=8)

        ctk.CTkButton(
            self,
            text="✕",
            width=36,
            height=28,
            fg_color="#45475a",
            hover_color="#f38ba8",
            text_color="#cdd6f4",
            font=ctk.CTkFont(size=13),
            command=lambda: on_delete(key_str)
        ).pack(side="right", padx=(0, 4), pady=8)


# ─────────────────────────────────────────────
# GUI — 멀티 키 선택 다이얼로그
# ─────────────────────────────────────────────
class KeySelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.title("키 선택")
        self.geometry("980x520")
        self.minsize(860, 460)
        self.configure(fg_color="#1e1e2e")
        self.transient(parent)
        self.grab_set()

        self.selected_keys: list[str] = []
        self._selected_set: set[str] = set()
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._selected_var = tk.StringVar(value="선택된 키: 없음")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="설정할 키를 클릭해서 고르세요",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#cdd6f4"
        ).pack(anchor="w", padx=20, pady=(18, 6))

        ctk.CTkLabel(
            self,
            text="여러 키를 한 번에 선택할 수 있고, 확인을 누르면 같은 소리가 모두에 등록됩니다.",
            font=ctk.CTkFont(size=13),
            text_color="#a6adc8"
        ).pack(anchor="w", padx=20)

        ctk.CTkLabel(
            self,
            textvariable=self._selected_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#89b4fa",
            justify="left",
            wraplength=900
        ).pack(fill="x", padx=20, pady=(14, 8))

        keyboard_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#181825",
            corner_radius=12,
            scrollbar_button_color="#313244",
            scrollbar_button_hover_color="#45475a"
        )
        keyboard_frame.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        for row in KEYBOARD_LAYOUT:
            row_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=6, pady=2)

            for label, key_str in row:
                button = ctk.CTkButton(
                    row_frame,
                    text=label,
                    width=key_button_width(label),
                    height=42,
                    corner_radius=10,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    command=lambda value=key_str: self._toggle_key(value)
                )
                button.pack(side="left", padx=4, pady=4)
                self._buttons[key_str] = button
                self._refresh_button(key_str)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 18))

        ctk.CTkButton(
            footer,
            text="선택 해제",
            width=110,
            height=38,
            fg_color="#45475a",
            hover_color="#585b70",
            text_color="#cdd6f4",
            command=self._clear_selection
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text="취소",
            width=90,
            height=38,
            fg_color="#313244",
            hover_color="#45475a",
            text_color="#cdd6f4",
            command=self._cancel
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            footer,
            text="확인",
            width=120,
            height=38,
            fg_color="#89b4fa",
            hover_color="#74c7ec",
            text_color="#1e1e2e",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._confirm
        ).pack(side="right")

    def _toggle_key(self, key_str: str) -> None:
        if key_str in self._selected_set:
            self._selected_set.remove(key_str)
        else:
            self._selected_set.add(key_str)
        self._refresh_button(key_str)
        self._update_selection_text()

    def _refresh_button(self, key_str: str) -> None:
        button = self._buttons[key_str]
        if key_str in self._selected_set:
            button.configure(
                fg_color="#89b4fa",
                hover_color="#74c7ec",
                text_color="#1e1e2e"
            )
        else:
            button.configure(
                fg_color="#313244",
                hover_color="#45475a",
                text_color="#cdd6f4"
            )

    def _ordered_keys(self) -> list[str]:
        return sort_keys(list(self._selected_set))

    def _update_selection_text(self) -> None:
        ordered_keys = self._ordered_keys()
        if not ordered_keys:
            self._selected_var.set("선택된 키: 없음")
            return

        self._selected_var.set(
            f"선택된 키 ({len(ordered_keys)}개): {format_key_list(ordered_keys)}"
        )

    def _clear_selection(self) -> None:
        for key_str in list(self._selected_set):
            self._selected_set.remove(key_str)
            self._refresh_button(key_str)
        self._update_selection_text()

    def _confirm(self) -> None:
        ordered_keys = self._ordered_keys()
        if not ordered_keys:
            messagebox.showwarning("선택 필요", "최소 1개의 키를 선택해 주세요.")
            return
        self.selected_keys = ordered_keys
        self.destroy()

    def _cancel(self) -> None:
        self.selected_keys = []
        self.destroy()


# ─────────────────────────────────────────────
# GUI — 메인 앱
# ─────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#181825")

        self.title("Key Sound Mapper")
        self.geometry("600x560")
        self.minsize(480, 400)

        self._store = MappingStore()
        self._engine = SoundEngine()
        self._key_listener = GlobalKeyListener(self._on_global_key)
        self._key_listener.start()
        self._tray: pystray.Icon | None = None
        self._tray_thread: threading.Thread | None = None

        for path in set(self._store.all().values()):
            self._engine.load(path)

        self._build_ui()
        self._refresh_list()

        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

    # ── UI 구성 ──────────────────────────────
    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="#181825", height=64)
        header.pack(fill="x", padx=20, pady=(20, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🎹  Key Sound Mapper",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#cdd6f4"
        ).pack(side="left")

        self._active_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            header,
            text="활성화",
            variable=self._active_var,
            command=self._toggle_active,
            font=ctk.CTkFont(size=13),
            text_color="#a6adc8",
            progress_color="#a6e3a1"
        ).pack(side="right")

        self._status_var = tk.StringVar(value="준비 완료")
        ctk.CTkLabel(
            self,
            textvariable=self._status_var,
            font=ctk.CTkFont(size=12),
            text_color="#6c7086",
            anchor="w"
        ).pack(fill="x", padx=24, pady=(4, 0))

        ctk.CTkFrame(self, height=1, fg_color="#313244").pack(
            fill="x", padx=20, pady=(8, 0)
        )

        ctk.CTkButton(
            self,
            text="＋  키 추가",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#89b4fa",
            hover_color="#74c7ec",
            text_color="#1e1e2e",
            command=self._add_mapping
        ).pack(fill="x", padx=20, pady=(14, 8))

        ctk.CTkLabel(
            self,
            text="매핑된 키",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#6c7086",
            anchor="w"
        ).pack(fill="x", padx=24)

        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#181825",
            scrollbar_button_color="#313244",
            scrollbar_button_hover_color="#45475a"
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=20, pady=(4, 16))

    def _refresh_list(self) -> None:
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        mappings = self._store.all()
        if not mappings:
            ctk.CTkLabel(
                self._scroll_frame,
                text="아직 매핑이 없어요.\n'키 추가' 버튼으로 시작해봐요!",
                font=ctk.CTkFont(size=14),
                text_color="#45475a",
                justify="center"
            ).pack(pady=60)
            return

        for key_str, sound_path in mappings.items():
            MappingRow(
                self._scroll_frame,
                key_str=key_str,
                sound_path=sound_path,
                on_delete=self._delete_mapping,
                on_test=self._test_sound
            ).pack(fill="x", pady=4)

    # ── 매핑 추가 / 삭제 / 테스트 ────────────
    def _add_mapping(self) -> None:
        dialog = KeySelectionDialog(self)
        self.wait_window(dialog)
        selected_keys = dialog.selected_keys
        if not selected_keys:
            return

        path = filedialog.askopenfilename(
            title="소리 파일 선택",
            filetypes=[
                ("오디오 파일", "*.wav *.mp3 *.ogg *.flac *.aiff"),
                ("모든 파일", "*.*")
            ]
        )
        if not path:
            return

        existing_keys = [
            key_str for key_str in selected_keys
            if self._store.get_sound(key_str)
        ]
        if existing_keys:
            key_text = format_key_list(existing_keys)
            should_continue = messagebox.askyesno(
                "덮어쓰기 확인",
                f"이미 등록된 키가 있어요.\n\n{key_text}\n\n기존 매핑을 덮어쓸까요?"
            )
            if not should_continue:
                return

        if not self._engine.load(path):
            messagebox.showerror("오류", f"소리 파일을 불러올 수 없어:\n{path}")
            return

        self._store.add_many(selected_keys, path)
        self._refresh_list()

        if len(selected_keys) == 1:
            self._set_status(
                f"'{display_key_name(selected_keys[0])}' 키에 '{Path(path).name}' 등록 완료"
            )
        else:
            self._set_status(
                f"{len(selected_keys)}개 키에 '{Path(path).name}' 등록 완료"
            )

    def _delete_mapping(self, key_str: str) -> None:
        sound_path = self._store.get_sound(key_str)
        self._store.remove(key_str)
        if sound_path and not self._store.has_sound_path(sound_path):
            self._engine.unload(sound_path)
        self._refresh_list()
        self._set_status(f"'{display_key_name(key_str)}' 매핑 삭제됨")

    def _test_sound(self, sound_path: str) -> None:
        self._engine.play(sound_path)
        self._set_status(f"테스트 재생: {Path(sound_path).name}")

    # ── 글로벌 키 이벤트 ──────────────────────
    def _on_global_key(self, key) -> None:
        key_str = key_to_str(key)
        sound_path = self._store.get_sound(key_str)
        if sound_path:
            self._engine.play(sound_path)
            self.after(0, lambda: self._set_status(
                f"🔊  '{display_key_name(key_str)}' → {Path(sound_path).name}"
            ))

    # ── 활성화 토글 ───────────────────────────
    def _toggle_active(self) -> None:
        is_active = self._active_var.get()
        self._key_listener.active = is_active
        self._set_status("키 감지 활성화" if is_active else "키 감지 비활성화")
        if self._tray:
            self._tray.icon = make_tray_icon(is_active)

    def _set_status(self, msg: str) -> None:
        self._status_var.set(msg)

    # ── 트레이 관련 ───────────────────────────
    def _hide_to_tray(self) -> None:
        """창을 숨기고 트레이 아이콘으로 이동."""
        self.withdraw()
        if self._tray is None:
            self._start_tray()

    def _start_tray(self) -> None:
        is_active = self._active_var.get()

        menu = pystray.Menu(
            pystray.MenuItem("열기", self._show_from_tray, default=True),
            pystray.MenuItem(
                "활성화",
                self._tray_toggle_active,
                checked=lambda item: self._active_var.get()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", self._quit_app),
        )

        self._tray = pystray.Icon(
            name="KeySoundMapper",
            icon=make_tray_icon(is_active),
            title="Key Sound Mapper",
            menu=menu
        )

        self._tray_thread = threading.Thread(
            target=self._tray.run, daemon=True
        )
        self._tray_thread.start()

    def _show_from_tray(self, icon=None, item=None) -> None:
        """트레이에서 창 다시 열기."""
        self.after(0, self.deiconify)

    def _tray_toggle_active(self, icon=None, item=None) -> None:
        """트레이 메뉴에서 활성화/비활성화 토글."""
        new_val = not self._active_var.get()
        self._active_var.set(new_val)
        self._key_listener.active = new_val
        self._set_status("키 감지 활성화" if new_val else "키 감지 비활성화")
        if self._tray:
            self._tray.icon = make_tray_icon(new_val)

    def _quit_app(self, icon=None, item=None) -> None:
        """완전 종료."""
        if self._tray:
            self._tray.stop()
        self._key_listener.stop()
        self._engine.quit()
        self.after(0, self.destroy)


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()