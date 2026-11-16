#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ДОЛБАЗАВР RPG — текстовая RPG с ASCII-графикой."""

import json
import os
import random
import sys
import time

APP_NAME = "Dolbazavr RPG"
VERSION = "1.0.0"

# Подключаемый ввод: окно игры подставляет сюда объект с методом getch().
backend = None
TEXT_SPEED = 1.0


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """Portable-сборка (рядом лежит portable.txt) и запуск из исходников хранят данные рядом с игрой."""
    base = app_dir()
    if getattr(sys, "frozen", False) and not os.path.exists(os.path.join(base, "portable.txt")):
        base = os.path.join(os.environ.get("APPDATA", base), APP_NAME)
    os.makedirs(base, exist_ok=True)
    return base


class C:
    RESET = "\033[0m"
    GREY = "\033[0;90m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"
    BRED = "\033[0;91m"
    BGREEN = "\033[0;92m"
    BYELLOW = "\033[0;93m"
    BBLUE = "\033[0;94m"
    BMAGENTA = "\033[0;95m"
    BCYAN = "\033[0;96m"
    BWHITE = "\033[0;97m"
    HERO = "\033[1;93m"
    BOSS = "\033[1;91m"


def c(text, color):
    return f"{color}{text}{C.RESET}"


# ---------------------------------------------------------------- ввод/вывод

_RU = "йцукенгшщзхъфывапролджэячсмитьбю"
_EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,."
LAYOUT = str.maketrans(_RU + _RU.upper(), _EN + _EN.upper())
ARROWS = {"Up": "w", "Down": "s", "Left": "a", "Right": "d"}


def getch():
    """Читает одну клавишу; русская раскладка и стрелки приводятся к WASD."""
    if backend is not None:
        sys.stdout.flush()
        ch = backend.getch()
        return ARROWS.get(ch) or ch.translate(LAYOUT).lower()
    if not sys.stdin.isatty():
        s = input()
        return s[:1].translate(LAYOUT).lower() if s else "\r"
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": "w", "P": "s", "K": "a", "M": "d"}.get(msvcrt.getwch(), "")
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch.translate(LAYOUT).lower()
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            return {"[A": "w", "[B": "s", "[D": "a", "[C": "d"}.get(sys.stdin.read(2), "")
        if ch == "\x03":
            raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch.translate(LAYOUT).lower()


def clear():
    sys.stdout.write("\033[H\033[2J\033[3J")
    sys.stdout.flush()


def pause(text="Нажмите любую клавишу..."):
    print(c(f"\n  {text}", C.GREY))
    getch()


def read_line(prompt="", maxlen=16):
    if backend is None:
        return input(prompt)
    sys.stdout.write(prompt)
    sys.stdout.flush()
    buf = ""
    while True:
        ch = backend.getch()
        if ch in ("\r", "\n"):
            return buf
        if ch == "\b":
            if buf:
                buf = buf[:-1]
                sys.stdout.write("\b")
        elif len(ch) == 1 and ch.isprintable() and len(buf) < maxlen:
            buf += ch
            sys.stdout.write(ch)
        sys.stdout.flush()


def typewrite(text, delay=0.012, color=C.WHITE):
    delay *= TEXT_SPEED
    sys.stdout.write(color)
    if delay <= 0:
        sys.stdout.write(text)
    else:
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
    sys.stdout.write(C.RESET + "\n")


def bar(cur, mx, width=20, color=C.BRED):
    cur = max(0, cur)
    filled = int(round(width * cur / mx)) if mx else 0
    return "[" + c("#" * filled, color) + c("-" * (width - filled), C.GREY) + "]"


def menu(options):
    return "   ".join(f"{c('[' + k + ']', C.BYELLOW)} {t}" for k, t in options)


# ------------------------------------------------------------------- графика

def art(s):
    return s.strip("\n").split("\n")


TITLE_LETTERS = {
    "D": [" ____  ", "|  _ \\ ", "| | | |", "| |_| |", "|____/ "],
    "-": ["       ", "       ", " _____ ", "|_____|", "       "],
    "R": [" ____  ", "|  _ \\ ", "| |_) |", "|  _ < ", "|_| \\_\\"],
    "E": [" _____ ", "| ____|", "|  _|  ", "| |___ ", "|_____|"],
    "X": ["__  __", "\\ \\/ /", " \\  / ", " /  \\ ", "/_/\\_\\"],
}

HERO_ART = art(r'''
               __
              / _)
     _.----._/ /
    /         /
 __/ (  | (  |
/__.-'|_|--|_|
''')

SLIME = art(r'''
      .-""""-.
     /  o  o  \
    |    __    |
    |   \__/   |
     '--------'
''')

BAT = art(r'''
   /\                 /\
  / \'._   (\_/)   _.'/ \
 /_.''._'--('.')--'_.''._\
 | \_ / `;=/ " \=;` \ _/ |
  \/ `\__|`\___/`|__/`  \/
          \(/|\)/
''')

CAVEMAN = art(r'''
      ,,,,,
     ( o o )        __
     (  -  )       /  \
   __/`---'\__    |    |
  /  |     |  \___|    |
 (   |     |       \__/
  \  |_____|
     /  |  \
    /__/ \__\
''')

GOBLIN = art(r'''
   __     .----.     __
   \ `.  / _  _ \  .' /
    `. \| (o)(o) |/ .'
      `-|   /\   |-'
        |  ____  |
         \ \/\/ /
       .--`----'--.
      /  | |  | |  \
''')

SKELETON = art(r'''
      .-.
     (o.o)
      |=|
     __|__
   //.=|=.\\
  // .=|=. \\
  \\ .=|=. //
   \\(_=_)//
    (:| |:)
     || ||
    ==' '==
''')

PTERO = art(r'''
 __                     __
 \ `-._      __     _.-' /
  \    `-.  / o>_.-'    /
   `-.    `/  /     _.-'
      `-._/  /  _.-'
          \_/-'
''')

TROLL = art(r'''
        _.-------._
      .'  _     _  '.
     /   (o)   (o)   \
    |       ___       |
    |   ,_/VVV\_,     |
     \   \^^^^^/     /
      '._  ---   _.'
       /`-------`\
      /  |     |  \
''')

RIVAL = art(r'''
     __
    (_ \
      \ \_.----._
       \         \
        |  ) |  ) \__
        |_|--|_|'-.__\
''')

GOLEM = art(r'''
      ___________
     / ##  ##  ##\
    | (@)     (@) |
    |    _____    |
     \  |#####|  /
   ___\_________/___
  /###|   ###   |###\
 /####|_________|####\
''')

MIMIC = art(r'''
     ____________
    |\  o    o   \
    | \___________\
    | |VVVVVVVVVVV|
    | |^^^^^^^^^^^|
     \|___________|
''')

METEOR = art(r'''
            .  *   .      *
       *   _.-""""-._   .
     .   .'  .   .   '.     *
        /  ( O )  ( O ) \
   *   |    .  ____  .   |
       |   .  /VVVV\    .| *
        \     \^^^^/    /
    *    '.  .  .  .  .'   .
   ~~~~~~~~`-.______.-'~~~~~~
  ~~~ ~~~~ ~~~ ~~~~~ ~~ ~~~ ~~
''')

VILLAGE_ART = art(r'''
         (  )   (   )  )
          ) (    )  (  (
          (  )  (    )  )
       ____||____________
      /\   ||            \
     /  \  ||   ______    \
    /____\_||__|      |____\
    | [] |     |  ()  | [] |
    |____|_____|______|____|
''')

TOMBSTONE = art(r'''
            _______
          /         \
         /   R.I.P.  \
        |             |
        |   ДОЛБА-    |
        |    ЗАВР     |
        |             |
        |  "был туп,  |
        |   но смел"  |
     ___|_____________|___
''')


# ---------------------------------------------------------------- данные мира

MAP = [
    "############################################",
    "#^^^^......TTTTT.......~~~~......TTTT..^^^^#",
    "#^^.......TTTTTT..?....~~~~.....TTTTTT.^^B^#",
    "#^....H....TTTT........~~~~.......TTTT..^.^#",
    "#......................~~~~.......?.....^.^#",
    "#......TT..............~~~~...^^^.......^.^#",
    "#.....TTTT.......TTTT..~~~~..^^^^^.........#",
    "#....TTTTTT..?....TT...~~~~...^^^...TTTT...#",
    "#.....TTTT.............====.......TTTTTTTT.#",
    "#......TT.......~~~....~~~~.......TTTT..?..#",
    "#..............~~~~~...~~~~..............TT#",
    "#...?....TT.....~~~....~~~~...TT...^^.....T#",
    "#.......TTTT...........~~~~..TTTT.^^^^.....#",
    "#^^.....TT.......TTT...~~~~...TT...^^....^^#",
    "#^^^^...........TTTTT..~~~~..?.........^^^^#",
    "############################################",
]

TILES = {
    ".": (C.GREEN, "."),
    "T": (C.BGREEN, "T"),
    "~": (C.BBLUE, "~"),
    "^": (C.WHITE, "^"),
    "H": (C.BYELLOW, "H"),
    "?": (C.BMAGENTA, "?"),
    "B": (C.BOSS, "B"),
    "=": (C.YELLOW, "="),
    "#": (C.GREY, "#"),
}
BLOCKED = "~^#"

REGIONS = {
    1: ("Папоротниковые луга", C.BGREEN),
    2: ("Костяные холмы", C.BYELLOW),
    3: ("Вулканический край", C.BRED),
}


def region(x):
    if x < 27:
        return 1
    if x < 36:
        return 2
    return 3


WEAPONS = [
    ("Голые зубы", 0, 0),
    ("Костяная дубина", 4, 40),
    ("Каменный топор", 8, 100),
    ("Обсидиановый клык", 14, 220),
    ("Хвост-булава", 22, 400),
]
ARMORS = [
    ("Родная чешуя", 0, 0),
    ("Шкура мамонта", 3, 50),
    ("Панцирь анкилозавра", 7, 130),
    ("Драконья чешуя", 12, 280),
]
POTION_PRICE = 15

ENEMIES = {
    1: [
        dict(name="Болотный слизень", art=SLIME, hp=18, atk=7, df=0, xp=8, gold=6),
        dict(name="Летучая мышь", art=BAT, hp=14, atk=9, df=1, xp=9, gold=5),
        dict(name="Пещерный человек", art=CAVEMAN, hp=26, atk=9, df=2, xp=14, gold=12),
    ],
    2: [
        dict(name="Гоблин-ворюга", art=GOBLIN, hp=40, atk=15, df=4, xp=24, gold=20),
        dict(name="Скелет", art=SKELETON, hp=48, atk=17, df=6, xp=30, gold=24),
        dict(name="Птеродактиль", art=PTERO, hp=42, atk=20, df=3, xp=34, gold=26),
    ],
    3: [
        dict(name="Пещерный тролль", art=TROLL, hp=95, atk=26, df=9, xp=65, gold=50),
        dict(name="Тираннозавр-задира", art=RIVAL, hp=115, atk=29, df=11, xp=85, gold=65),
        dict(name="Магмовый голем", art=GOLEM, hp=130, atk=27, df=15, xp=90, gold=70),
    ],
}
MIMIC_FOE = dict(name="Мимик", art=MIMIC, hp=50, atk=16, df=5, xp=40, gold=60)
BOSS_FOE = dict(name="МЕТЕОР ПОГИБЕЛИ", art=METEOR, hp=420, atk=38, df=14, xp=0, gold=0)

SAVE_FILE = os.path.join(data_dir(), "dolbazavr_save.json")


# ---------------------------------------------------------------------- герой

class Player:
    def __init__(self, name="Долбазавр"):
        self.name = name
        self.lvl = 1
        self.xp = 0
        self.max_hp = 50
        self.hp = 50
        self.base_atk = 8
        self.base_def = 3
        self.gold = 20
        self.potions = 2
        self.weapon = 0
        self.armor = 0
        self.x, self.y = 6, 4
        self.opened = []
        self.kills = 0
        self.steps = 0

    @property
    def atk(self):
        return self.base_atk + WEAPONS[self.weapon][1]

    @property
    def df(self):
        return self.base_def + ARMORS[self.armor][1]

    @property
    def xp_next(self):
        return 15 * self.lvl * (self.lvl + 1)

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def gain_xp(self, amount):
        msgs = []
        self.xp += amount
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.lvl += 1
            self.max_hp += 12
            self.base_atk += 3
            self.base_def += 1
            self.hp = self.max_hp
            msgs.append(f"*** НОВЫЙ УРОВЕНЬ {self.lvl}! HP +12, Атака +3, Защита +1 ***")
        return msgs

    @classmethod
    def from_dict(cls, d):
        p = cls()
        p.__dict__.update(d)
        return p


def save_game(p):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(vars(p), f, ensure_ascii=False, indent=1)


def load_game():
    if not os.path.exists(SAVE_FILE):
        return None
    with open(SAVE_FILE, encoding="utf-8") as f:
        return Player.from_dict(json.load(f))


# ------------------------------------------------------------------------ бой

def roll(base):
    return random.randint(int(base * 0.8), max(int(base * 0.8), int(base * 1.2)))


def draw_battle(p, e, rage, log, is_boss):
    clear()
    ecol = C.BOSS if is_boss else C.BRED
    print()
    left = f"  {c(p.name.upper(), C.HERO)}  Ур.{p.lvl}"
    print(left + " " * (40 - len(p.name) - len(str(p.lvl)) - 7) + c(e["name"], ecol))
    print(f"  HP     {bar(p.hp, p.max_hp, 14, C.BGREEN)} {p.hp:>3}/{p.max_hp:<4}"
          f"       HP {bar(e['hp'], e['max_hp'], 14, C.BRED)} {max(0, e['hp'])}/{e['max_hp']}")
    print(f"  Ярость {bar(rage, 100, 14, C.BYELLOW)} {rage:>3}")
    print()

    hero = HERO_ART
    foe = e["art"]
    height = max(len(hero), len(foe))
    hero = [""] * (height - len(hero)) + hero
    foe = [""] * (height - len(foe)) + foe
    for i in range(height):
        mid = c("  VS  ", C.BWHITE) if i == height - 3 else "      "
        print("  " + c(hero[i].ljust(20), C.BGREEN) + mid + c(foe[i], ecol))
    print()
    print(c("  " + "-" * 66, C.GREY))
    for line in log[-5:]:
        print("  " + line)
    for _ in range(5 - len(log[-5:])):
        print()
    print(c("  " + "-" * 66, C.GREY))
    special = "Долбо-удар" if rage >= 40 else c("Долбо-удар", C.GREY)
    opts = [("1", "Атака"), ("2", special), ("3", "Защита"), ("4", f"Зелье x{p.potions}")]
    if not is_boss:
        opts.append(("5", "Бежать"))
    print("  " + menu(opts))


def battle(p, template, is_boss=False):
    """Возвращает 'win', 'flee' или 'dead'."""
    e = dict(template)
    if not is_boss:
        bonus = random.uniform(0.9, 1.15)
        e["hp"] = int(e["hp"] * bonus)
    e["max_hp"] = e["hp"]
    rage = 0
    charging = False
    turn = 0
    log = [c(f"На вас напал {e['name']}!", C.BWHITE)]
    if is_boss:
        log = [c("Небо пылает. МЕТЕОР ПОГИБЕЛИ открывает свои огненные глаза!", C.BOSS)]

    while True:
        draw_battle(p, e, rage, log, is_boss)
        key = getch()
        defending = False

        if key == "1":
            dmg = max(1, roll(p.atk) - e["df"])
            if random.random() < 0.12:
                dmg *= 2
                log.append(c(f"КРИТ! Вы кусаете {e['name']} на {dmg} урона!", C.BYELLOW))
            else:
                log.append(f"Вы кусаете {e['name']} на {c(dmg, C.BWHITE)} урона.")
            e["hp"] -= dmg
            rage = min(100, rage + 15)
        elif key == "2":
            if rage < 40:
                log.append(c("Не хватает ярости! Нужно 40.", C.GREY))
                continue
            rage -= 40
            dmg = int(roll(p.atk) * 2.5)
            e["hp"] -= dmg
            log.append(c(f"ДОЛБО-УДАР!!! Вы бьёте лбом со всей дури: {dmg} урона!", C.BYELLOW))
        elif key == "3":
            defending = True
            rage = min(100, rage + 25)
            log.append(c("Вы прячете голову и упираетесь хвостом.", C.BCYAN))
        elif key == "4":
            if p.potions <= 0:
                log.append(c("Зелий нет!", C.GREY))
                continue
            p.potions -= 1
            healed = p.heal(int(p.max_hp * 0.5))
            log.append(c(f"Вы пьёте зелье из папоротника: +{healed} HP.", C.BGREEN))
        elif key == "5" and not is_boss:
            if random.random() < 0.6:
                log.append("Вы позорно, но эффективно убегаете.")
                draw_battle(p, e, rage, log, is_boss)
                pause()
                return "flee"
            log.append(c("Вы споткнулись о собственный хвост! Сбежать не вышло.", C.RED))
        else:
            continue

        if e["hp"] <= 0:
            log.append(c(f"{e['name']} повержен!", C.BGREEN))
            draw_battle(p, e, rage, log, is_boss)
            pause()
            return "win"

        turn += 1
        if charging:
            charging = False
            mult = 3 if is_boss else 2
            dmg = max(1, roll(e["atk"]) * mult - p.df)
            if defending:
                dmg = max(1, int(dmg * 0.35))
            name = "ОГНЕННЫЙ ДОЖДЬ" if is_boss else "МОЩНЫЙ УДАР"
            note = " (вы защитились)" if defending else ""
            log.append(c(f"{e['name']}: {name}! {dmg} урона{note}!", C.BOSS))
            p.hp -= dmg
        elif (is_boss and turn % 3 == 0) or (not is_boss and random.random() < 0.18):
            charging = True
            if is_boss:
                log.append(c("Метеор раскаляется добела... Сейчас рванёт! (защищайтесь!)", C.BRED))
            else:
                log.append(c(f"{e['name']} готовит мощный удар! (защищайтесь!)", C.BRED))
        elif random.random() < 0.08:
            log.append(f"{e['name']} промахивается!")
        else:
            dmg = max(1, roll(e["atk"]) - p.df)
            if defending:
                dmg = max(1, int(dmg * 0.35))
            log.append(c(f"{e['name']} наносит вам {dmg} урона.", C.RED))
            p.hp -= dmg

        if p.hp <= 0:
            p.hp = 0
            draw_battle(p, e, rage, log, is_boss)
            pause()
            return "dead"


def reward(p, e):
    p.kills += 1
    gold = e["gold"] + random.randint(0, e["gold"] // 2 + 1)
    p.gold += gold
    clear()
    print()
    print(c("  === ПОБЕДА! ===", C.BGREEN))
    print()
    print(f"  Опыт:   +{c(e['xp'], C.BCYAN)}")
    print(f"  Золото: +{c(gold, C.BYELLOW)}")
    if random.random() < 0.2:
        p.potions += 1
        print(f"  Добыча: {c('Зелье из папоротника', C.BGREEN)}")
    for msg in p.gain_xp(e["xp"]):
        print()
        print("  " + c(msg, C.HERO))
    pause()


# ---------------------------------------------------------------------- экраны

def game_over():
    clear()
    print()
    for line in TOMBSTONE:
        print(c(line, C.GREY))
    print()
    print(c("            ВЫ ПОГИБЛИ", C.BRED))
    print(c("   Мир съеден тьмой, а ваш скелет поставят в музей.", C.GREY))
    pause()


def ending(p):
    clear()
    print()
    for line in HERO_ART:
        print("        " + c(line, C.BGREEN))
    print()
    typewrite("  Метеор Погибели рассыпался на тысячу тлеющих камешков.", 0.02)
    typewrite("  Учёные потом назовут это 'вымиранием', но мы-то знаем правду:", 0.02)
    typewrite(f"  {p.name} просто долбанул его лбом.", 0.02, C.HERO)
    print()
    print(c("  ============  ПОБЕДА!  ============", C.BYELLOW))
    print(f"  Уровень: {p.lvl}   Убито врагов: {p.kills}   Шагов: {p.steps}")
    pause()


def status_screen(p):
    clear()
    print()
    print(c("  === ГЕРОЙ ===", C.HERO))
    print()
    info = [
        f"Имя:     {p.name}",
        f"Уровень: {p.lvl}",
        f"HP:      {p.hp}/{p.max_hp}",
        f"Опыт:    {p.xp}/{p.xp_next}",
        f"Атака:   {p.atk}  (база {p.base_atk})",
        f"Защита:  {p.df}  (база {p.base_def})",
        f"Оружие:  {WEAPONS[p.weapon][0]}",
        f"Броня:   {ARMORS[p.armor][0]}",
        f"Золото:  {p.gold}",
        f"Зелья:   {p.potions}",
        f"Убито:   {p.kills}",
    ]
    for i in range(max(len(info), len(HERO_ART))):
        a = HERO_ART[i] if i < len(HERO_ART) else ""
        t = info[i] if i < len(info) else ""
        print("  " + c(a.ljust(22), C.BGREEN) + "  " + t)
    pause()


def help_screen():
    clear()
    print(c("""
  === КАК ИГРАТЬ ===
""", C.HERO))
    print("""  Вы — Долбазавр, самый тупой, но самый храбрый динозавр.
  Где-то в Вулканическом краю (буква B на карте) упал МЕТЕОР ПОГИБЕЛИ.
  Победите его, пока он не устроил вымирание.

  Управление на карте:  WASD или стрелки — идти,  I — герой,  Q — в меню.
  Русская раскладка тоже работает.

  В бою:
    Атака      — обычный укус, копит ярость.
    Долбо-удар — тратит 40 ярости, бьёт в 2.5 раза сильнее и игнорирует броню.
    Защита     — снижает урон в ~3 раза и даёт много ярости.
                 Используйте, когда враг готовит мощный удар!
    Зелье      — лечит половину здоровья.

  Чем дальше на восток, тем опаснее враги. В деревне (H) можно
  отдохнуть, закупиться и сохраниться. Сундуки (?) бывают... кусачими.""")
    pause()


def shop(p):
    msg = ""
    while True:
        clear()
        print()
        print(c("  === ЛАВКА СТАРОГО ТРИЦЕРАТОПСА ===", C.BYELLOW))
        print(c("  \"Покупай, малыш, пока не вымер.\"", C.GREY))
        print()
        print(f"  Золото: {c(p.gold, C.BYELLOW)}   Атака: {p.atk}   Защита: {p.df}   Зелья: {p.potions}")
        print()
        print(f"  {c('[1]', C.BYELLOW)} Зелье из папоротника (+50% HP) ......... {POTION_PRICE} з.")
        if p.weapon + 1 < len(WEAPONS):
            n, a, price = WEAPONS[p.weapon + 1]
            print(f"  {c('[2]', C.BYELLOW)} Оружие: {n} (атака +{a}) ".ljust(55, ".") + f" {price} з.")
        else:
            print(c("  [2] Оружие: у вас лучшее, что есть", C.GREY))
        if p.armor + 1 < len(ARMORS):
            n, d, price = ARMORS[p.armor + 1]
            print(f"  {c('[3]', C.BYELLOW)} Броня: {n} (защита +{d}) ".ljust(55, ".") + f" {price} з.")
        else:
            print(c("  [3] Броня: у вас лучшая, что есть", C.GREY))
        print(f"  {c('[0]', C.BYELLOW)} Назад")
        print()
        if msg:
            print("  " + msg)
        key = getch()
        if key == "0":
            return
        if key == "1":
            if p.gold >= POTION_PRICE:
                p.gold -= POTION_PRICE
                p.potions += 1
                msg = c("Куплено зелье.", C.BGREEN)
            else:
                msg = c("Не хватает золота.", C.RED)
        elif key == "2" and p.weapon + 1 < len(WEAPONS):
            n, _, price = WEAPONS[p.weapon + 1]
            if p.gold >= price:
                p.gold -= price
                p.weapon += 1
                msg = c(f"Теперь у вас {n}!", C.BGREEN)
            else:
                msg = c("Не хватает золота.", C.RED)
        elif key == "3" and p.armor + 1 < len(ARMORS):
            n, _, price = ARMORS[p.armor + 1]
            if p.gold >= price:
                p.gold -= price
                p.armor += 1
                msg = c(f"Теперь на вас {n}!", C.BGREEN)
            else:
                msg = c("Не хватает золота.", C.RED)


def village(p):
    msg = ""
    while True:
        clear()
        print()
        for line in VILLAGE_ART:
            print("  " + c(line, C.YELLOW))
        print()
        print(c("  === ДЕРЕВНЯ ГНИЛОЙ ПАПОРОТНИК ===", C.BYELLOW))
        print(f"  HP: {p.hp}/{p.max_hp}   Золото: {p.gold}   Зелья: {p.potions}")
        print()
        inn_price = 5 * p.lvl
        print("  " + menu([("1", f"Таверна: отдых ({inn_price} з.)"), ("2", "Лавка")]))
        print("  " + menu([("3", "Сохранить игру"), ("0", "Уйти")]))
        print()
        if msg:
            print("  " + msg)
        key = getch()
        if key == "0":
            return
        if key == "1":
            if p.hp == p.max_hp:
                msg = c("Вы и так бодры, как молодой раптор.", C.GREY)
            elif p.gold >= inn_price:
                p.gold -= inn_price
                p.hp = p.max_hp
                msg = c("Вы храпите так, что трясутся горы. HP восстановлено!", C.BGREEN)
            else:
                msg = c("Трактирщик-игуанодон косо смотрит: денег нет.", C.RED)
        elif key == "2":
            shop(p)
            msg = ""
        elif key == "3":
            save_game(p)
            msg = c("Игра сохранена (выбито на каменной табличке).", C.BGREEN)


def open_chest(p, tier):
    p.opened.append([p.x, p.y])
    if random.random() < 0.15:
        clear()
        print()
        print(c("  Сундук распахивает пасть, полную зубов! ЭТО МИМИК!", C.BRED))
        pause()
        result = battle(p, MIMIC_FOE)
        if result == "win":
            reward(p, MIMIC_FOE)
        return result
    kind = random.choice(["gold", "gold", "potion", "atk", "def", "hp"])
    if kind == "gold":
        g = random.randint(20, 50) * tier
        p.gold += g
        return f"В сундуке {g} золотых!"
    if kind == "potion":
        n = random.randint(1, 2)
        p.potions += n
        return f"В сундуке зелья: {n} шт.!"
    if kind == "atk":
        p.base_atk += 2
        return "Древний зуб тираннозавра! Атака +2 навсегда."
    if kind == "def":
        p.base_def += 1
        return "Кусок прочного панциря! Защита +1 навсегда."
    p.max_hp += 10
    p.hp += 10
    return "Чудо-корешок! Максимальное HP +10."


# ------------------------------------------------------------------------ карта

def draw_map(p, msg):
    clear()
    reg = region(p.x)
    rname, rcol = REGIONS[reg]
    panel = [
        c(f"{p.name.upper()}  Ур. {p.lvl}", C.HERO),
        f"HP  {bar(p.hp, p.max_hp, 12, C.BGREEN)} {p.hp}/{p.max_hp}",
        f"XP  {bar(p.xp, p.xp_next, 12, C.BCYAN)} {p.xp}/{p.xp_next}",
        f"Атака: {p.atk}   Защита: {p.df}",
        f"Золото: {c(p.gold, C.BYELLOW)}   Зелья: {c(p.potions, C.BGREEN)}",
        f"Оружие: {WEAPONS[p.weapon][0]}",
        f"Броня:  {ARMORS[p.armor][0]}",
        "",
        f"Местность: {c(rname, rcol)}",
        f"Опасность: {c('*' * reg, rcol)}",
        "",
        c("Легенда:", C.GREY),
        f"{c('@', C.HERO)} вы   {c('H', C.BYELLOW)} деревня  {c('?', C.BMAGENTA)} сундук",
        f"{c('T', C.BGREEN)} лес  {c('~', C.BBLUE)} вода     {c('^', C.WHITE)} горы",
        f"{c('=', C.YELLOW)} мост {c('B', C.BOSS)} ЛОГОВО МЕТЕОРА",
        "",
    ]
    print()
    for y, row in enumerate(MAP):
        out = []
        cur = None
        for x, ch in enumerate(row):
            if (x, y) == (p.x, p.y):
                col, sym = C.HERO, "@"
            else:
                if ch == "?" and [x, y] in p.opened:
                    ch = "."
                col, sym = TILES[ch]
            if col != cur:
                out.append(col)
                cur = col
            out.append(sym)
        out.append(C.RESET)
        print("  " + "".join(out) + "   " + (panel[y] if y < len(panel) else ""))
    print()
    print("  " + (msg or ""))
    print()
    print("  " + menu([("WASD/стрелки", "идти"), ("I", "герой"), ("H", "помощь"), ("Q", "выход")]))


def explore(p):
    msg = c("Вы выходите из деревни. Пахнет серой и приключениями.", C.BWHITE)
    while True:
        draw_map(p, msg)
        msg = ""
        key = getch()
        moves = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}
        if key == "i":
            status_screen(p)
            continue
        if key == "h":
            help_screen()
            continue
        if key == "q":
            clear()
            print()
            print("  Выйти в главное меню? Несохранённый прогресс пропадёт.")
            print("  " + menu([("1", "Да"), ("2", "Нет")]))
            if getch() == "1":
                return
            continue
        if key not in moves:
            continue

        dx, dy = moves[key]
        nx, ny = p.x + dx, p.y + dy
        tile = MAP[ny][nx]
        if tile in BLOCKED:
            msg = c({"~": "Вы не умеете плавать. Вы динозавр, а не плезиозавр.",
                     "^": "Слишком круто. Ваши ручки слишком короткие для скалолазания.",
                     "#": "Край мира. Дальше только пустота и плоскоземельцы."}[tile], C.GREY)
            continue
        if tile == "B":
            clear()
            print()
            for line in METEOR:
                print("  " + c(line, C.BOSS))
            print()
            print(c("  Земля дрожит. Воздух плавится. Впереди — МЕТЕОР ПОГИБЕЛИ.", C.BRED))
            print(c("  Пути назад не будет.", C.BRED))
            print()
            print("  " + menu([("1", "В бой!"), ("2", "Я ещё не готов")]))
            if getch() != "1":
                msg = "Вы благоразумно отступаете. Это на вас не похоже."
                continue
            result = battle(p, BOSS_FOE, is_boss=True)
            if result == "win":
                ending(p)
            else:
                game_over()
            return

        p.x, p.y = nx, ny
        p.steps += 1

        if tile == "H":
            village(p)
            msg = "Вы покидаете деревню."
            continue
        if tile == "?" and [nx, ny] not in p.opened:
            result = open_chest(p, region(nx))
            if result == "dead":
                game_over()
                return
            if result == "flee":
                msg = "Вы удрали от мимика, а сундук обиженно уполз."
            elif result == "win":
                msg = "Мимик побеждён!"
            else:
                msg = c(result, C.BMAGENTA)
            continue

        chance = 0.18 if tile == "T" else 0.08 if tile == "." else 0
        if random.random() < chance:
            foe = random.choice(ENEMIES[region(nx)])
            result = battle(p, foe)
            if result == "dead":
                game_over()
                return
            if result == "win":
                reward(p, foe)
                msg = "Победа! Вы гордо рычите на всю округу."
            else:
                msg = "Вы оторвались от погони."


# ---------------------------------------------------------------- титульный экран

def title_screen():
    clear()
    print("\n")
    width = 79
    word = "D-REX"
    for row in range(5):
        line = "  ".join(TITLE_LETTERS[ch][row] for ch in word)
        print(c(line.center(width).rstrip(), C.HERO))
    print()
    print(c("Д О Л Б А З А В Р    R P G".center(width).rstrip(), C.BYELLOW))
    print("\n")
    pad = " " * ((width - max(map(len, HERO_ART))) // 2)
    for line in HERO_ART:
        print(pad + c(line, C.BGREEN))
    print("\n")
    opts = [("1", "Новая игра"), ("2", "Загрузить")]
    if not os.path.exists(SAVE_FILE):
        opts[1] = ("2", c("Загрузить", C.GREY))
    print(" " * 18 + menu(opts + [("3", "Выход")]))
    print("\n\n")
    print(c(f"v{VERSION}  (c) Долбазавр Студиос".center(width).rstrip(), C.GREY))


def new_game():
    clear()
    print()
    print(c("  Как зовут вашего динозавра?", C.BWHITE))
    print(c("  (Enter — оставить «Долбазавр»)", C.GREY))
    name = read_line("\n  > ").strip()[:16] or "Долбазавр"
    p = Player(name)
    clear()
    print()
    typewrite("  Давным-давно, в эпоху, когда папоротники были большими...", 0.02)
    typewrite("  ...с неба рухнул МЕТЕОР ПОГИБЕЛИ.", 0.02, C.BRED)
    typewrite("  Он упал в Вулканическом краю, и из трещин полезла всякая нечисть.", 0.02)
    typewrite("  Все умные динозавры сразу спрятались.", 0.02)
    typewrite(f"  Но {name} не был умным.", 0.02, C.HERO)
    typewrite(f"  {name} был ДОЛБАЗАВРОМ.", 0.04, C.HERO)
    pause()
    help_screen()
    return p


def main():
    while True:
        title_screen()
        key = getch()
        if key == "1":
            explore(new_game())
        elif key == "2":
            p = load_game()
            if p:
                explore(p)
        elif key in ("3", "q"):
            clear()
            print(c("\n  Пока! Не вымирайте.\n", C.BYELLOW))
            return


def run_console():
    if os.name == "nt":
        os.system("")  # включает ANSI-цвета в консоли Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        main()
    except KeyboardInterrupt:
        print(C.RESET + "\n  Пока!")


if __name__ == "__main__":
    run_console()
