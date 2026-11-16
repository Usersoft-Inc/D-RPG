"""Тематическое окно без рамки: терминал с ANSI-цветами, свой заголовок и настройки."""

import ctypes
import json
import os
import queue
import re
import sys
import threading
import traceback
import tkinter as tk
import tkinter.font as tkfont

import game

COLS, ROWS = 81, 28
PADX, PADY = 10, 6
ESC_RE = re.compile(r"\x1b\[([0-9;]*)([A-Za-z])")
IS_WIN = os.name == "nt"

SETTINGS_FILE = os.path.join(game.data_dir(), "settings.json")
DEFAULTS = {
    "font_size": 0,
    "theme": "classic",
    "speed": 1.0,
    "opacity": 100,
    "topmost": False,
    "fullscreen": False,
}
SPEEDS = [(0.0, "Мгновенно"), (0.5, "Быстро"), (1.0, "Обычно"), (2.0, "Медленно")]
ANSI_CODES = ["90", "31", "32", "33", "34", "35", "36", "37",
              "91", "92", "93", "94", "95", "96", "97"]


def _phosphor(name, bg, dim, mid, bright, top):
    level = {"90": dim, "34": dim}
    colors = {k: level.get(k, mid if k.startswith("3") else bright) for k in ANSI_CODES}
    return dict(name=name, bg=bg, fg=mid, bold=top, accent=bright, dim=dim,
                bar=bg, hover="#1a1a1a", colors=colors)


THEMES = {
    "classic": dict(
        name="Классика", bg="#000000", fg="#c8c8c8", bold=None, accent="#3fdc5a",
        dim="#4d6b4f", bar="#060d07", hover="#13301a",
        colors={
            "90": "#6e6e6e", "31": "#d04040", "32": "#3fae49", "33": "#c9a227",
            "34": "#3d6fd8", "35": "#b452c8", "36": "#2fb5a8", "37": "#c8c8c8",
            "91": "#ff5f5f", "92": "#5fff7f", "93": "#ffe066", "94": "#6fa8ff",
            "95": "#ff7af2", "96": "#66f2ff", "97": "#ffffff",
        },
    ),
    "green": _phosphor("Зелёный ЭЛТ", "#010a03", "#1d6b2c", "#34b84c", "#5cf27a", "#c0ffcc"),
    "amber": _phosphor("Янтарный ЭЛТ", "#0a0600", "#7a4f00", "#c98400", "#ffb21f", "#ffe2a0"),
}


def on_click(widget, fn):
    """Срабатывает при отпускании кнопки мыши над виджетом, как у обычной кнопки."""
    def release(e):
        if 0 <= e.x < widget.winfo_width() and 0 <= e.y < widget.winfo_height():
            fn()
    widget.bind("<ButtonRelease-1>", release)


def resource(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def load_settings():
    s = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            s.update({k: v for k, v in json.load(f).items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    if s["theme"] not in THEMES:
        s["theme"] = "classic"
    return s


def work_area(root):
    if IS_WIN:
        class RECT(ctypes.Structure):
            _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                        ("r", ctypes.c_long), ("b", ctypes.c_long)]
        r = RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):
            return r.l, r.t, r.r - r.l, r.b - r.t
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


class GameIO:
    """Мост между потоком игры и окном: клавиши в одну сторону, текст — в другую."""

    encoding = "utf-8"

    def __init__(self):
        self.keys = queue.Queue()
        self.out = queue.Queue()
        self._buf = []

    def getch(self):
        return self.keys.get()

    def write(self, s):
        self._buf.append(s)
        return len(s)

    def flush(self):
        if self._buf:
            self.out.put("".join(self._buf))
            self._buf.clear()

    def isatty(self):
        return False


class Terminal(tk.Text):
    def __init__(self, master):
        super().__init__(master, wrap="none", width=COLS, height=ROWS, bd=0,
                         highlightthickness=0, padx=PADX, pady=PADY, cursor="arrow",
                         takefocus=0, exportselection=False, state="disabled")
        self.tag = None
        for seq in ("<Button-1>", "<B1-Motion>", "<Double-1>", "<Triple-1>"):
            self.bind(seq, lambda e: "break")

    def apply_theme(self, theme, font, bold):
        self.configure(bg=theme["bg"], fg=theme["fg"], font=font,
                       selectbackground=theme["bg"], inactiveselectbackground=theme["bg"])
        self.tag_configure("bold", font=bold, foreground=theme["bold"] or theme["fg"])
        for code, color in theme["colors"].items():
            self.tag_configure("c" + code, foreground=color)
            self.tag_configure("c" + code + "b", foreground=theme["bold"] or color, font=bold)

    def feed(self, data):
        cut = data.rfind("\x1b[2J")
        if cut != -1:
            data = data[cut:]
        self.configure(state="normal")
        pos = 0
        for m in ESC_RE.finditer(data):
            self._text(data[pos:m.start()])
            params, cmd = m.groups()
            if cmd == "m":
                self._sgr(params)
            elif cmd == "J":
                self.delete("1.0", "end")
            pos = m.end()
        self._text(data[pos:])
        self.configure(state="disabled")

    def _text(self, s):
        for i, part in enumerate(s.split("\b")):
            if i:
                self.delete("end-2c")
            if part:
                self.insert("end", part, self.tag or ())

    def _sgr(self, params):
        bold, color = False, None
        for code in (params or "0").split(";"):
            if code in ("", "0"):
                bold, color = False, None
            elif code == "1":
                bold = True
            else:
                color = code
        if color:
            self.tag = "c" + color + ("b" if bold else "")
        else:
            self.tag = "bold" if bold else None


class App:
    def __init__(self):
        if IS_WIN:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except (AttributeError, OSError):
                pass
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DolbazavrStudios.DolbazavrRPG")
            except (AttributeError, OSError):
                pass

        self.s = load_settings()
        self.io = GameIO()
        self.game_done = False
        self.panel = None

        self.root = root = tk.Tk()
        root.withdraw()
        root.title("Долбазавр RPG")
        root.overrideredirect(True)
        try:
            root.iconbitmap(default=resource("assets", "icon.ico"))
        except tk.TclError:
            pass

        families = set(tkfont.families(root))
        self.family = next((f for f in ("Consolas", "Cascadia Mono", "Lucida Console", "Courier New")
                            if f in families), "TkFixedFont")
        self.font = tkfont.Font(root, family=self.family, size=12)
        self.bold = tkfont.Font(root, family=self.family, size=12, weight="bold")
        self.small = tkfont.Font(root, family=self.family, size=9)
        self.icons = {}
        for px in (16, 24, 32, 48):
            try:
                self.icons[px] = tk.PhotoImage(master=root, file=resource("assets", f"icon_{px}.png"))
            except tk.TclError:
                pass

        self.body = tk.Frame(root)
        self.body.pack(fill="both", expand=True, padx=1, pady=1)
        self.bar = tk.Frame(self.body)
        self.bar_icon = tk.Label(self.bar)
        self.bar_title = tk.Label(self.bar, text="ДОЛБАЗАВР RPG")
        self.bar_hint = tk.Label(self.bar, text=f"v{game.VERSION}   F2 настройки · F11 полный экран")
        self.btn_close = self._bar_button("✕", self.quit, danger=True)
        self.btn_min = self._bar_button("—", self.minimize)
        self.btn_cfg = self._bar_button("≡", self.toggle_settings)
        self.bar_icon.pack(side="left", padx=(8, 4))
        self.bar_title.pack(side="left")
        self.bar_hint.pack(side="left", padx=12)
        for b in (self.btn_close, self.btn_min, self.btn_cfg):
            b.pack(side="right", fill="y")
        for w in (self.bar, self.bar_icon, self.bar_title, self.bar_hint):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

        self.wrap = tk.Frame(self.body)
        self.term = Terminal(self.wrap)
        self.term.pack(expand=True)

        root.bind("<Key>", self.on_key)
        root.bind("<Map>", lambda e: root.after(10, root.focus_force))

        self.apply_settings(first=True)
        root.deiconify()
        self._show_in_taskbar()
        root.focus_force()

        game.backend = self.io
        sys.stdout = self.io
        threading.Thread(target=self._run_game, daemon=True).start()
        self._pump()

    # ------------------------------------------------------------ заголовок

    def _bar_button(self, text, cmd, danger=False):
        b = tk.Label(self.bar, text=text, width=4, cursor="hand2")
        b.danger = danger
        on_click(b, cmd)
        b.bind("<Enter>", lambda e: b.configure(bg="#c42b1c" if b.danger else self.t["hover"],
                                                fg="#ffffff" if b.danger else self.t["accent"]))
        b.bind("<Leave>", lambda e: b.configure(bg=self.t["bar"], fg=self.t["accent"]))
        return b

    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        if not self.s["fullscreen"]:
            self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _hwnd(self):
        return ctypes.windll.user32.GetParent(self.root.winfo_id())

    def _show_in_taskbar(self):
        if not IS_WIN:
            return
        self.root.update_idletasks()
        hwnd = self._hwnd()
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        style = (style & ~0x00000080) | 0x00040000  # -TOOLWINDOW, +APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
        self.root.withdraw()
        self.root.after(10, self.root.deiconify)

    def minimize(self):
        if IS_WIN:
            ctypes.windll.user32.ShowWindow(self._hwnd(), 6)
        else:
            self.root.iconify()

    def quit(self):
        self.save_settings()
        self.root.destroy()

    # ------------------------------------------------------------ настройки

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.s, f, ensure_ascii=False, indent=1)
        except OSError:
            pass

    @property
    def t(self):
        return THEMES[self.s["theme"]]

    def _fits(self, size, max_w, max_h, with_bar):
        f = tkfont.Font(self.root, family=self.family, size=size)
        w = f.measure("0") * COLS + 2 * PADX + 2
        h = f.metrics("linespace") * ROWS + 2 * PADY + 2
        if with_bar:
            h += tkfont.Font(self.root, family=self.family, size=self._bar_size(size),
                             weight="bold").metrics("linespace") + 8
        return w <= max_w and h <= max_h

    def _best_size(self, max_w, max_h, with_bar, cap=40):
        for size in range(cap, 6, -1):
            if self._fits(size, max_w, max_h, with_bar):
                return size
        return 7

    @staticmethod
    def _bar_size(size):
        return max(9, round(size * 0.8))

    def apply_settings(self, first=False):
        s, t, root = self.s, self.t, self.root
        game.TEXT_SPEED = s["speed"]
        ax, ay, aw, ah = work_area(root)
        full = s["fullscreen"]
        if full:
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            size = self._best_size(sw, sh, False)
        else:
            limit = self._best_size(aw, ah, True)
            want = s["font_size"] or self._best_size(int(aw * 0.85), int(ah * 0.85), True, cap=22)
            size = min(want, limit)
        self.cur_size = size

        self.font.configure(size=size)
        self.bold.configure(size=size)
        bar_size = self._bar_size(size)
        bar_font = tkfont.Font(root, family=self.family, size=bar_size, weight="bold")
        self.small.configure(size=max(8, bar_size - 2))

        root.configure(bg=t["accent"] if not full else t["bg"])
        self.body.configure(bg=t["bg"])
        self.wrap.configure(bg=t["bg"])
        self.bar.configure(bg=t["bar"])
        icon_px = min(self.icons, key=lambda p: abs(p - bar_font.metrics("linespace")), default=None)
        self.bar_icon.configure(bg=t["bar"], image=self.icons.get(icon_px, ""))
        self.bar_title.configure(bg=t["bar"], fg=t["accent"], font=bar_font)
        self.bar_hint.configure(bg=t["bar"], fg=t["dim"], font=self.small)
        for b in (self.btn_close, self.btn_min, self.btn_cfg):
            b.configure(bg=t["bar"], fg=t["accent"], font=bar_font)
        self.term.apply_theme(t, self.font, self.bold)

        self.bar.pack_forget()
        self.wrap.pack_forget()
        if not full:
            self.bar.pack(fill="x")
        self.wrap.pack(fill="both", expand=True)
        self.body.pack_configure(padx=0 if full else 1, pady=0 if full else 1)

        root.attributes("-alpha", s["opacity"] / 100)
        root.attributes("-topmost", s["topmost"] or full)
        root.update_idletasks()
        if full:
            root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
        else:
            w, h = root.winfo_reqwidth(), root.winfo_reqheight()
            root.geometry(f"{w}x{h}+{ax + (aw - w) // 2}+{ay + (ah - h) // 2}")
        if self.panel is not None:
            self._build_panel()
        if not first:
            self.save_settings()

    def toggle_settings(self):
        if self.panel is None:
            self._build_panel()
        else:
            self.panel.destroy()
            self.panel = None

    def _set(self, key, value):
        self.s[key] = value
        self.apply_settings()

    def _opt(self, parent, text, cmd, active=False):
        t = self.t
        b = tk.Label(parent, text=text, font=self.bold if active else self.font, bg=t["bg"],
                     fg=t["accent"] if active else t["fg"], cursor="hand2", padx=4)
        on_click(b, cmd)
        b.bind("<Enter>", lambda e: b.configure(bg=t["hover"]))
        b.bind("<Leave>", lambda e: b.configure(bg=t["bg"]))
        return b

    def _build_panel(self):
        if self.panel is not None:
            self.panel.destroy()
        t, s = self.t, self.s
        outer = tk.Frame(self.wrap, bg=t["accent"], padx=1, pady=1)
        p = tk.Frame(outer, bg=t["bg"], padx=self.font.measure("00"), pady=self.font.metrics("linespace") // 2)
        p.pack()
        self.panel = outer

        tk.Label(p, text="=== НАСТРОЙКИ ===", font=self.bold, bg=t["bg"], fg=t["accent"]).grid(
            row=0, column=0, columnspan=2, pady=(0, self.font.metrics("linespace") // 2))

        def row(r, label):
            tk.Label(p, text=label, font=self.font, bg=t["bg"], fg=t["fg"], anchor="w").grid(
                row=r, column=0, sticky="w", padx=(0, self.font.measure("00")))
            f = tk.Frame(p, bg=t["bg"])
            f.grid(row=r, column=1, sticky="w")
            return f

        f = row(1, "Размер шрифта")
        self._opt(f, "[-]", lambda: self._set("font_size", max(7, self.cur_size - 1))).pack(side="left")
        tk.Label(f, text=f"{self.cur_size:>3}", font=self.bold, bg=t["bg"], fg=t["accent"]).pack(side="left")
        self._opt(f, "[+]", lambda: self._set("font_size", self.cur_size + 1)).pack(side="left")
        self._opt(f, "(*) Под экран" if not s["font_size"] else "( ) Под экран",
                  lambda: self._set("font_size", 0), active=not s["font_size"]).pack(side="left", padx=(12, 0))

        f = row(2, "Тема")
        for key, th in THEMES.items():
            on = s["theme"] == key
            self._opt(f, ("(*) " if on else "( ) ") + th["name"], lambda k=key: self._set("theme", k),
                      active=on).pack(side="left")

        f = row(3, "Скорость текста")
        for value, label in SPEEDS:
            on = s["speed"] == value
            self._opt(f, ("(*) " if on else "( ) ") + label, lambda v=value: self._set("speed", v),
                      active=on).pack(side="left")

        f = row(4, "Прозрачность")
        self._opt(f, "[-]", lambda: self._set("opacity", max(50, s["opacity"] - 10))).pack(side="left")
        tk.Label(f, text=f"{s['opacity']:>3}%", font=self.bold, bg=t["bg"], fg=t["accent"]).pack(side="left")
        self._opt(f, "[+]", lambda: self._set("opacity", min(100, s["opacity"] + 10))).pack(side="left")

        f = row(5, "Поверх всех окон")
        self._opt(f, "[x]" if s["topmost"] else "[ ]", lambda: self._set("topmost", not s["topmost"]),
                  active=s["topmost"]).pack(side="left")

        f = row(6, "Полный экран")
        self._opt(f, "[x]" if s["fullscreen"] else "[ ]", self.toggle_fullscreen,
                  active=s["fullscreen"]).pack(side="left")
        tk.Label(f, text=" F11", font=self.small, bg=t["bg"], fg=t["dim"]).pack(side="left")

        tk.Label(p, text=f"Сохранения: {game.data_dir()}", font=self.small, bg=t["bg"], fg=t["dim"]).grid(
            row=7, column=0, columnspan=2, pady=(self.font.metrics("linespace") // 2, 0))
        self._opt(p, "[ Готово ]", self.toggle_settings, active=True).grid(
            row=8, column=0, columnspan=2, pady=(self.font.metrics("linespace") // 2, 0))

        outer.place(relx=0.5, rely=0.5, anchor="center")

    def toggle_fullscreen(self):
        self._set("fullscreen", not self.s["fullscreen"])

    # ---------------------------------------------------------------- ввод

    def on_key(self, e):
        ks = e.keysym
        if ks == "F11":
            self.toggle_fullscreen()
            return "break"
        if ks == "F2":
            self.toggle_settings()
            return "break"
        if self.panel is not None:
            if ks == "Escape":
                self.toggle_settings()
            return "break"
        if ks == "Escape" and self.s["fullscreen"]:
            self.toggle_fullscreen()
            return "break"
        if self.io.keys.qsize() >= 2:
            return "break"
        if ks in ("Up", "Down", "Left", "Right"):
            self.io.keys.put(ks)
        elif ks in ("Return", "KP_Enter"):
            self.io.keys.put("\r")
        elif ks == "BackSpace":
            self.io.keys.put("\b")
        elif e.char and e.char.isprintable():
            self.io.keys.put(e.char)
        return "break"

    # ----------------------------------------------------------- поток игры

    def _run_game(self):
        try:
            game.main()
        except Exception:
            err = traceback.format_exc()
            try:
                with open(os.path.join(game.data_dir(), "crash.log"), "w", encoding="utf-8") as f:
                    f.write(err)
            except OSError:
                pass
            self.io.write("\x1b[H\x1b[2J\x1b[0;91m  Динозавр споткнулся об ошибку и упал :(\n\n\x1b[0;37m"
                          + err + "\n\x1b[0;90m  Отчёт сохранён в crash.log. Нажмите любую клавишу.")
            self.io.flush()
            self.io.keys.get()
        self.game_done = True

    def _pump(self):
        chunks = []
        while True:
            try:
                chunks.append(self.io.out.get_nowait())
            except queue.Empty:
                break
        if chunks:
            self.term.feed("".join(chunks))
        if self.game_done:
            self.quit()
            return
        self.root.after(15, self._pump)


def run():
    app = App()
    app.root.mainloop()
