#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
matrix.py — Python / ncurses port of Matrix 2.0.

Original: Turbo Pascal 5.5, Alexander Demin, MAI dept. 302, 1995.
Sources: MATRICS.PAS and friends in this directory.

Demonstrates basic matrix operations interactively in a text-mode UI
that mirrors the DOS original: a blue sidebar of push-buttons on the
left, a dark-grey workspace on the right where matrices are drawn with
animated colouring as operations run.

Operations:
  * Ввод             — input matrix A or B (digit entry, resize with Alt-arrows)
  * Равенство        — compare A and B element-wise
  * Сложение         — A + B (requires equal sizes)
  * Умножение на число — multiply A by a scalar
  * Умножение матриц — A * B (requires A.cols == B.rows)
  * Транспонирование — transpose A in place
  * Идентификация    — identify type: zero / diagonal / identity /
                        symmetric / skew-symmetric / triangular / singular
  * Задержка         — set animation delay (ms)
  * О программе      — about box
  * Выход            — exit

Navigation:
  ↑/↓ or Tab/Shift-Tab   move through menu
  Enter                  activate
  Latin-letter hotkeys   activate (V-input, E-equality, A-add, N-scalar,
                                   M-matmul, T-transpose, I-ident,
                                   D-delay, O-about, X-exit)
  Esc                    cancel / exit

Requirements: UTF-8 terminal, ≥ 16 colours, ≥ 80×25.
Run: ./matrix.py    (chmod +x first)   or   uv run matrix.py
"""

from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass, field
from typing import Callable

# ─── DOS colour palette ────────────────────────────────────────────────
BLACK, BLUE, GREEN, CYAN, RED, MAGENTA, BROWN, LGRAY = range(8)
DGRAY, LBLUE, LGREEN, LCYAN, LRED, LMAGENTA, YELLOW, WHITE = range(8, 16)

# ─── Screen / layout constants (mirrored from COMMON.PAS) ──────────────
SCR_W, SCR_H = 80, 25
MAIN_BACK_X = 25
MAIN_BACK_Y = 1
START_X = 2

MAX_INP_STR = 4
WIN_MAT_X = 5
WIN_MAT_Y = 5
ELEM_SIZE_X = MAX_INP_STR + 1  # 5
WIN_MAT_SIZE_X = ELEM_SIZE_X * WIN_MAT_X  # 25
MAT_ELEM_OFS = 12
MAT_TITLE_OFS = 12

MAT_X = MAIN_BACK_X
MAT_Y = MAIN_BACK_Y + 1

MAT_CH_LEFT = WIN_MAT_SIZE_X + 3  # 28
MAT_CH_RIGHT = MAT_CH_LEFT + 26  # 54
MAT_CH_BOTTOM = 6
MAT_OFS_RC = MAT_CH_LEFT + 21  # 49

MAX_MAT_COL = 20
MAX_MAT_ROW = 20
MAX_MAT_VAL = 9.9
MIN_MAT_VAL = -9.9

REP_LEFT = MAIN_BACK_X + 1  # 26
REP_RIGHT = SCR_W - 2  # 78
REP_TOP = SCR_H - 3  # 22

TWO_AX = MAIN_BACK_X + 4  # 29
TWO_AY = MAIN_BACK_Y + 2  # 3 (tweaked to fit 25-row screen)
TWO_BX = TWO_AX
TWO_BY = TWO_AY + WIN_MAT_Y + 3  # 11

THR_AX = MAIN_BACK_X + 4  # 29
THR_AY = MAIN_BACK_Y + 0  # 1
THR_BX = THR_AX
THR_BY = THR_AY + WIN_MAT_Y + 2  # 8
THR_CX = THR_AX
THR_CY = THR_BY + WIN_MAT_Y + 2  # 15

IDN_X = TWO_AX
IDN_Y = TWO_AY

DELAY_MIN = 0
DELAY_MAX = 200

FRAME = "┌┐┘└│─"  # TL, TR, BR, BL, V, H — as in WINS.PAS/SingleFrame
BAR_CHAR = "░"
RUN_CHAR = "■"


# ─── Menu text & hotkeys ───────────────────────────────────────────────
MAIN_BUTTONS = [
    ("Ввод", "V"),
    ("Равенство", "E"),
    ("Сложение", "A"),
    ("Умножение на число", "N"),
    ("Умножение матриц", "M"),
    ("Транспонирование", "T"),
    ("Идентификация", "I"),
    ("Задержка", "D"),
    ("О программе", "O"),
    ("Выход", "X"),
]
(
    CM_INPUT,
    CM_EQU,
    CM_ADD,
    CM_MULTN,
    CM_MULTM,
    CM_TRANS,
    CM_IDENT,
    CM_DELAY,
    CM_ABOUT,
    CM_EXIT,
) = range(1, 11)

CHECK_BUTTONS = [
    ("Нуль-матрица", "N"),
    ("Диагональная", "D"),
    ("Единичная", "E"),
    ("Симметрическая", "S"),
    ("Кососимметрическая", "K"),
    ("Треугольная", "T"),
    ("Вырожденная", "G"),
    ("Возврат в меню", "B"),
]

TITLE = "* Matrix  Version 2.0 *"

ABOUT_LINES = [
    "Matrix",
    "Демонстрационная программа",
    "работы с матрицами",
    "Версия 2.0 (Python/curses port)",
    "Автор: Александр Демин",
    "МАИ, Кафедра 302, 1995",
]


# ─── Colour pair management ────────────────────────────────────────────
class Pal:
    """Look up a curses attribute for a (fg, bg) pair in the DOS palette."""

    def __init__(self) -> None:
        self.pairs: dict[tuple[int, int], int] = {}
        self.next = 1

    def setup(self) -> None:
        curses.start_color()
        if curses.COLORS < 16:
            # Fall back: map 8–15 onto 0–7; brightness is lost but colour
            # survives.
            self.remap = lambda c: c & 7
        else:
            self.remap = lambda c: c

    def attr(self, fg: int, bg: int) -> int:
        key = (self.remap(fg), self.remap(bg))
        pair = self.pairs.get(key)
        if pair is None:
            pair = self.next
            self.next += 1
            try:
                curses.init_pair(pair, key[0], key[1])
            except curses.error:
                # Out of pairs — reuse pair 0.
                return 0
            self.pairs[key] = pair
        return curses.color_pair(pair)


PAL = Pal()


# ─── Low-level drawing helpers ─────────────────────────────────────────
class Screen:
    """Thin wrapper around curses that lets us draw by (x, y, ch, fg, bg)."""

    def __init__(self, stdscr: "curses._CursesWindow") -> None:
        self.win = stdscr
        self.h, self.w = stdscr.getmaxyx()

    def put(self, x: int, y: int, ch: str, fg: int, bg: int) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            try:
                self.win.addstr(y, x, ch, PAL.attr(fg, bg))
            except curses.error:
                pass  # bottom-right cell raises; safe to ignore

    def put_str(self, x: int, y: int, s: str, fg: int, bg: int) -> None:
        for i, ch in enumerate(s):
            self.put(x + i, y, ch, fg, bg)

    def fill(
        self, x1: int, y1: int, x2: int, y2: int, ch: str, fg: int, bg: int
    ) -> None:
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.put(x, y, ch, fg, bg)

    def box(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        fg: int,
        bg: int,
        frame: str = FRAME,
    ) -> None:
        for y in range(y1 + 1, y2):
            self.put(x1, y, frame[4], fg, bg)
            self.put(x2, y, frame[4], fg, bg)
        for x in range(x1 + 1, x2):
            self.put(x, y1, frame[5], fg, bg)
            self.put(x, y2, frame[5], fg, bg)
        self.put(x1, y1, frame[0], fg, bg)
        self.put(x2, y1, frame[1], fg, bg)
        self.put(x2, y2, frame[2], fg, bg)
        self.put(x1, y2, frame[3], fg, bg)

    def refresh(self) -> None:
        self.win.refresh()


# ─── "Hot key" coloured text (like DrawText in BUTTONS.PAS) ────────────
def draw_hot(
    scr: Screen,
    x: int,
    y: int,
    text: str,
    hot: str,
    fg: int,
    hotfg: int,
    bg: int,
) -> None:
    """Render text; colour the first occurrence of hot letter with hotfg."""
    hot_idx = text.lower().find(hot.lower())
    for i, ch in enumerate(text):
        scr.put(x + i, y, ch, hotfg if i == hot_idx else fg, bg)


def draw_button(
    scr: Screen,
    x: int,
    y: int,
    size: int,
    text: str,
    hot: str,
    pressed: bool,
    bg_btn: int,
    fg_txt: int,
    fg_hot: int,
    bg_around: int,
) -> None:
    """DOS-style 3-D push button, width=size, height=2 (shadow row)."""
    # clear slot
    scr.fill(x, y, x + size, y + 1, " ", bg_around, bg_around)
    bx = x + (1 if pressed else 0)
    for i in range(size):
        scr.put(bx + i, y, " ", bg_btn, bg_btn)
    if not pressed:
        # shadow
        for i in range(1, size + 1):
            scr.put(x + i, y + 1, "▀", bg_around, bg_around)  # top half block
        scr.put(x + size, y, "▄", bg_around, bg_around)
    # centre the label
    ofs = (size - len(text)) // 2
    draw_hot(scr, bx + ofs, y, text, hot, fg_txt, fg_hot, bg_btn)


# ─── Matrix state ──────────────────────────────────────────────────────
@dataclass
class Matrix:
    data: list[list[float]] = field(
        default_factory=lambda: [
            [0.0] * MAX_MAT_COL for _ in range(MAX_MAT_ROW)
        ]
    )
    cols: int = 5
    rows: int = 5

    def copy(self) -> "Matrix":
        m = Matrix(cols=self.cols, rows=self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                m.data[i][j] = self.data[i][j]
        return m


def fmt_cell(v: float) -> str:
    """1-decimal fixed-width (4 chars) as in RealToStr."""
    s = f"{v:4.1f}"
    return s[-MAX_INP_STR:]


# ─── Window / matrix display ───────────────────────────────────────────
@dataclass
class ViewAttrs:
    x: int = 1
    y: int = 1
    at: list[list[tuple[int, int]]] = field(
        default_factory=lambda: [
            [(LGRAY, BLUE)] * MAX_MAT_COL for _ in range(MAX_MAT_ROW)
        ]
    )


def draw_fill_box(scr: Screen, x1: int, y1: int, x2: int, y2: int) -> None:
    scr.box(x1, y1, x2, y2, WHITE, LGRAY)
    scr.fill(x1 + 1, y1 + 1, x2 - 1, y2 - 1, " ", LGRAY, LGRAY)


def show_mat(scr: Screen, x: int, y: int, m: Matrix, dt: ViewAttrs) -> None:
    draw_fill_box(scr, x, y, x + WIN_MAT_SIZE_X + 1, y + WIN_MAT_Y + 1)
    for i in range(MAX_MAT_ROW):
        for j in range(MAX_MAT_COL):
            dt.at[i][j] = (LGRAY, BLUE)
    dt.x = 1
    dt.y = 1
    scr.put_str(x + 2, y, " Элемент [     ] ", WHITE, LGRAY)
    show_n_pos(scr, x, y, 1, 1, LGRAY, BLUE, m, dt)


def show_col_row(scr: Screen, x: int, y: int, m: Matrix) -> None:
    scr.put_str(x + 2, y + WIN_MAT_Y + 1, " Матрица [     ] ", WHITE, LGRAY)
    scr.put_str(
        x + MAT_TITLE_OFS,
        y + WIN_MAT_Y + 1,
        f"{m.rows:2d},{m.cols:2d}",
        WHITE,
        LGRAY,
    )


def show_n_pos(
    scr: Screen,
    x: int,
    y: int,
    i: int,
    j: int,
    fg: int,
    bg: int,
    m: Matrix,
    dt: ViewAttrs,
) -> None:
    scr.put_str(x + MAT_ELEM_OFS, y, f"{i:2d},{j:2d}", WHITE, LGRAY)
    # clear empty strip when matrix smaller than window
    if m.cols < WIN_MAT_X:
        scr.fill(
            x + m.cols * ELEM_SIZE_X + 1,
            y + 1,
            x + WIN_MAT_SIZE_X,
            y + WIN_MAT_Y,
            " ",
            LGRAY,
            BLUE,
        )
    if m.rows < WIN_MAT_Y:
        scr.fill(
            x + 1,
            y + m.rows + 1,
            x + WIN_MAT_SIZE_X,
            y + WIN_MAT_Y,
            " ",
            LGRAY,
            BLUE,
        )
    dt.at[i - 1][j - 1] = (fg, bg)
    # scroll the view so (i,j) is visible
    if m.cols <= WIN_MAT_X:
        dt.x = 1
    else:
        if j >= dt.x + WIN_MAT_X:
            dt.x = j - WIN_MAT_X + 1
        if j < dt.x:
            dt.x = j
    if m.rows <= WIN_MAT_Y:
        dt.y = 1
    else:
        if i >= dt.y + WIN_MAT_Y:
            dt.y = i - WIN_MAT_Y + 1
        if i < dt.y:
            dt.y = i
    for ri in range(WIN_MAT_Y):
        for rj in range(WIN_MAT_X):
            rj_idx = rj + dt.x
            ri_idx = ri + dt.y
            if ri_idx <= m.rows and rj_idx <= m.cols:
                fg2, bg2 = dt.at[ri_idx - 1][rj_idx - 1]
                scr.put_str(
                    x + rj * ELEM_SIZE_X + 1,
                    y + ri + 1,
                    fmt_cell(m.data[ri_idx - 1][rj_idx - 1]),
                    fg2,
                    bg2,
                )


# ─── Background / workspace frame ──────────────────────────────────────
def draw_background(scr: Screen) -> None:
    scr.fill(0, 0, MAIN_BACK_X - 1, SCR_H - 1, " ", LBLUE, LBLUE)
    scr.box(0, 0, MAIN_BACK_X - 1, SCR_H - 1, WHITE, LBLUE)
    scr.fill(MAIN_BACK_X, MAIN_BACK_Y, SCR_W - 1, SCR_H - 1, " ", DGRAY, DGRAY)
    scr.fill(MAIN_BACK_X, 0, SCR_W - 1, MAIN_BACK_Y - 1, " ", LGRAY, LGRAY)
    scr.put_str(
        MAIN_BACK_X + (SCR_W - MAIN_BACK_X - len(TITLE)) // 2,
        0,
        TITLE,
        RED,
        LGRAY,
    )


def clear_main_box(scr: Screen) -> None:
    scr.fill(MAIN_BACK_X, MAIN_BACK_Y, SCR_W - 1, SCR_H - 1, " ", DGRAY, DGRAY)


def local_msg(scr: Screen, msg: str, wait_key: bool = False) -> None:
    draw_fill_box(scr, REP_LEFT, REP_TOP, REP_RIGHT, REP_TOP + 2)
    i = (REP_RIGHT - REP_LEFT - len(msg)) // 2
    scr.put_str(REP_LEFT + 1 + i, REP_TOP + 1, msg, BLACK, LGRAY)
    scr.refresh()
    if wait_key:
        scr.win.getch()


# ─── Menu (vertical, left sidebar) ─────────────────────────────────────
def draw_sidebar(
    scr: Screen, items: list[tuple[str, str]], selected: int
) -> None:
    # blank the whole sidebar except the outer frame
    scr.fill(1, 1, MAIN_BACK_X - 2, SCR_H - 2, " ", LBLUE, LBLUE)
    n = len(items)
    max_btn = max(len(t) for t, _ in items)
    for idx, (text, hot) in enumerate(items):
        y = (SCR_H - n * 2) // 2 + 2 * idx
        pressed = False
        color_bg = DGRAY if idx == selected else BLUE
        draw_button(
            scr,
            START_X,
            y,
            max_btn,
            text,
            hot,
            pressed,
            bg_btn=color_bg,
            fg_txt=WHITE,
            fg_hot=YELLOW,
            bg_around=LBLUE,
        )


def horizontal_menu(
    scr: Screen, items: list[tuple[str, str]], y: int, bg_around: int = RED
) -> int:
    n = len(items)
    max_btn = max(len(t) for t, _ in items)
    ofs = max_btn + 2
    xs = [(SCR_W - ofs * n) // 2 + ofs * i + 1 for i in range(n)]
    selected = 0

    def draw(idx: int, pressed: bool) -> None:
        for k in range(n):
            is_sel = k == idx
            bg = DGRAY if is_sel else BLUE
            text, hot = items[k]
            draw_button(
                scr,
                xs[k],
                y,
                max_btn,
                text,
                hot,
                pressed and is_sel,
                bg_btn=bg,
                fg_txt=WHITE,
                fg_hot=YELLOW,
                bg_around=bg_around,
            )

    while True:
        draw(selected, False)
        scr.refresh()
        k = scr.win.getch()
        if k in (curses.KEY_LEFT, curses.KEY_BTAB):
            selected = (selected - 1) % n
        elif k in (curses.KEY_RIGHT, curses.KEY_DOWN, 9):  # Tab/Right/Down
            selected = (selected + 1) % n
        elif k in (10, 13, curses.KEY_ENTER):
            draw(selected, True)
            scr.refresh()
            time.sleep(0.1)
            return selected + 1
        elif k == 27:
            return n  # last button = Cancel
        elif 32 <= k < 256:
            ch = chr(k).lower()
            for i, (_t, hot) in enumerate(items):
                if hot.lower() == ch:
                    draw(i, True)
                    scr.refresh()
                    time.sleep(0.1)
                    return i + 1


# ─── Message box ───────────────────────────────────────────────────────
def draw_win(scr: Screen, x1: int, y1: int, x2: int, y2: int) -> None:
    scr.fill(x1, y1, x2, y2, " ", WHITE, RED)
    scr.box(x1, y1, x2, y2, WHITE, RED)
    # shadow
    for x in range(x1 + 1, x2 + 2):
        scr.put(x, y2 + 1, " ", BLACK, BLACK)
    for y in range(y1 + 1, y2 + 2):
        scr.put(x2 + 1, y, " ", BLACK, BLACK)


def message_box(
    scr: Screen, lines: list[str], buttons: list[tuple[str, str]]
) -> int:
    n = len(buttons)
    but_len = max(len(t) for t, _ in buttons)
    max_len = max((len(s) for s in lines), default=0)
    size_x = max((but_len + 2) * n, max_len + 4)
    size_y = len(lines) + 5
    left = (SCR_W - size_x) // 2
    top = (SCR_H - size_y) // 2
    right = left + size_x
    bottom = top + size_y
    # snapshot for restore
    saved = [
        [(" ", 0, 0)] * (right - left + 3) for _ in range(bottom - top + 2)
    ]
    for yy in range(len(saved)):
        for xx in range(len(saved[0])):
            pass  # we just repaint background afterwards

    draw_win(scr, left, top, right, bottom)
    for i, text in enumerate(lines):
        scr.put_str(
            left + (size_x - len(text) + 1) // 2, top + i + 2, text, WHITE, RED
        )
    result = horizontal_menu(scr, buttons, top + len(lines) + 3, bg_around=RED)
    # repaint whatever was behind — cheap: redraw background & main box
    return result


# ─── Small helpers ─────────────────────────────────────────────────────
def sleep_ms(ms: int) -> None:
    if ms > 0:
        time.sleep(ms / 1000.0)


def getch_ex(scr: Screen) -> int:
    """getch() that turns arrow-keys and Esc into single codes."""
    return scr.win.getch()


# ─── Matrix input ──────────────────────────────────────────────────────
def input_number_inline(
    scr: Screen,
    x: int,
    y: int,
    initial: float,
    lo: float,
    hi: float,
    is_real: bool = True,
) -> tuple[bool, float]:
    """Read a number in-place; returns (ok, value). Esc cancels."""
    buf = (f"{initial:4.1f}" if is_real else f"{int(initial):4d}").strip()
    ptr = len(buf)
    curses.curs_set(1)
    while True:
        s = buf.ljust(MAX_INP_STR)[:MAX_INP_STR]
        scr.put_str(x, y, s, WHITE, BLUE)
        try:
            scr.win.move(y, x + min(ptr, MAX_INP_STR - 1))
        except curses.error:
            pass
        scr.refresh()
        k = scr.win.getch()
        if k == 27:  # Esc
            curses.curs_set(0)
            return False, initial
        if k in (10, 13, curses.KEY_ENTER, 9):  # Enter / Tab
            try:
                v = float(buf) if is_real else int(buf)
            except ValueError:
                curses.beep()
                message_box(
                    scr,
                    [
                        "ОШИБКА",
                        "Недопустимые символы в числе",
                        "Повторите ввод",
                    ],
                    [("ОК", "O")],
                )
                continue
            if not (lo <= v <= hi):
                curses.beep()
                message_box(
                    scr,
                    [
                        "ОШИБКА",
                        "Введённое число не лежит",
                        "в разрешённых пределах",
                        "Повторите ввод",
                    ],
                    [("ОК", "O")],
                )
                continue
            curses.curs_set(0)
            return True, v
        if k in (curses.KEY_BACKSPACE, 127, 8):
            if ptr > 0:
                ptr -= 1
                buf = buf[:ptr] + buf[ptr + 1 :]
            continue
        if k == curses.KEY_LEFT:
            ptr = max(0, ptr - 1)
            continue
        if k == curses.KEY_RIGHT:
            ptr = min(len(buf), ptr + 1)
            continue
        if 32 <= k < 128 and chr(k) in "0123456789.-":
            ch = chr(k)
            if len(buf) < MAX_INP_STR:
                buf = buf[:ptr] + ch + buf[ptr:]
                ptr += 1
            else:
                buf = buf[:ptr] + ch + buf[ptr + 1 :]
                ptr = min(ptr + 1, MAX_INP_STR)


def input_number_prompt(
    scr: Screen,
    msg: str,
    initial: float,
    lo: float,
    hi: float,
    is_real: bool = True,
) -> tuple[bool, float]:
    """Pop-up prompt (used for scalar mul / delay / random fill)."""
    NInpX = TWO_AX
    NInpY = TWO_AY + WIN_MAT_Y + 3
    NInpW = 40
    draw_fill_box(scr, NInpX, NInpY, NInpX + NInpW, NInpY + 2)
    scr.put_str(NInpX + 1, NInpY + 1, msg, BLACK, LGRAY)
    ok, v = input_number_inline(
        scr,
        NInpX + NInpW - MAX_INP_STR - 1,
        NInpY + 1,
        initial,
        lo,
        hi,
        is_real,
    )
    return ok, v


def fill_matrix(scr: Screen, m: Matrix, delay_ms: int) -> None:
    answer = message_box(
        scr,
        ["Каким образом будем заполнять матрицу?"],
        [("Числом", "N"), ("Случайным образом", "R"), ("Отмена", "C")],
    )
    if answer not in (1, 2):
        return
    dt = ViewAttrs()
    for i in range(MAX_MAT_ROW):
        for j in range(MAX_MAT_COL):
            dt.at[i][j] = (BLACK, LGRAY)
    if answer == 1:
        ok, n = input_number_prompt(
            scr, "Введите число для заполнения:", 1.0, MIN_MAT_VAL, MAX_MAT_VAL
        )
        if not ok:
            return
    local_msg(scr, "Идёт заполнение матрицы ...")
    for i in range(1, m.rows + 1):
        for j in range(1, m.cols + 1):
            show_n_pos(scr, MAT_X, MAT_Y, i, j, YELLOW, LGRAY, m, dt)
            scr.refresh()
            sleep_ms(delay_ms)
            if answer == 1:
                m.data[i - 1][j - 1] = n
            else:
                m.data[i - 1][j - 1] = random.randint(
                    int(MIN_MAT_VAL), int(MAX_MAT_VAL)
                )
            show_n_pos(scr, MAT_X, MAT_Y, i, j, LRED, LGRAY, m, dt)
            scr.refresh()
            sleep_ms(delay_ms)
    local_msg(scr, "Матрица заполнена")


def input_mat(scr: Screen, m: Matrix, delay_ms: int) -> None:
    i, j = 1, 1
    dt = ViewAttrs()
    while True:
        clear_main_box(scr)
        show_mat(scr, MAT_X, MAT_Y, m, dt)
        # side panel
        draw_fill_box(
            scr,
            MAT_X + MAT_CH_LEFT,
            MAT_Y,
            MAT_X + MAT_CH_RIGHT,
            MAT_Y + MAT_CH_BOTTOM,
        )
        scr.put_str(
            MAT_X + MAT_CH_LEFT + 2, MAT_Y + 1, "Кол-во строк", BLACK, LGRAY
        )
        scr.put_str(
            MAT_X + MAT_CH_LEFT + 2, MAT_Y + 2, "Кол-во столбцов", BLACK, LGRAY
        )
        scr.put_str(
            MAT_X + MAT_CH_LEFT + 2,
            MAT_Y + 4,
            "Alt-↑↓/←→: размер",
            BLACK,
            LGRAY,
        )
        scr.put_str(
            MAT_X + MAT_CH_LEFT + 2,
            MAT_Y + 5,
            "F7 заполнить, F10 OK",
            BLACK,
            LGRAY,
        )
        scr.put_str(MAT_X + MAT_OFS_RC, MAT_Y + 1, f"{m.rows:4d}", CYAN, LGRAY)
        scr.put_str(MAT_X + MAT_OFS_RC, MAT_Y + 2, f"{m.cols:4d}", CYAN, LGRAY)
        show_col_row(scr, MAT_X, MAT_Y, m)

        # loop of per-cell navigation
        while True:
            show_n_pos(scr, MAT_X, MAT_Y, i, j, WHITE, CYAN, m, dt)
            scr.put_str(
                MAT_X + MAT_OFS_RC, MAT_Y + 1, f"{m.rows:4d}", CYAN, LGRAY
            )
            scr.put_str(
                MAT_X + MAT_OFS_RC, MAT_Y + 2, f"{m.cols:4d}", CYAN, LGRAY
            )
            scr.refresh()
            k = scr.win.getch()
            dt.at[i - 1][j - 1] = (LGRAY, BLUE)
            if k == 27 or k == curses.KEY_F10:  # Esc / F10 → done
                break
            if k == curses.KEY_F7:
                fill_matrix(scr, m, delay_ms)
                break
            if k == curses.KEY_UP:
                i = max(1, i - 1)
                continue
            if k == curses.KEY_DOWN:
                i = min(m.rows, i + 1)
                continue
            if k == curses.KEY_LEFT:
                j -= 1
                if j < 1:
                    if i > 1:
                        i -= 1
                        j = m.cols
                    else:
                        j = 1
                continue
            if k == curses.KEY_RIGHT:
                j += 1
                if j > m.cols:
                    if i < m.rows:
                        i += 1
                        j = 1
                    else:
                        j = m.cols
                continue
            if k == 544 or k == curses.KEY_SLEFT:  # Alt-Left /dec cols
                m.cols = max(1, m.cols - 1)
                j = min(j, m.cols)
                break
            if k == curses.KEY_SRIGHT or k == 559:  # Alt-Right / inc cols
                m.cols = min(MAX_MAT_COL, m.cols + 1)
                break
            if k == 565 or k == curses.KEY_SR:  # Alt-Up / dec rows
                m.rows = max(1, m.rows - 1)
                i = min(i, m.rows)
                break
            if k == 524 or k == curses.KEY_SF:  # Alt-Down / inc rows
                m.rows = min(MAX_MAT_ROW, m.rows + 1)
                break
            if k == curses.KEY_F5:
                ok, v = input_number_inline(
                    scr,
                    MAT_X + MAT_OFS_RC + 1,
                    MAT_Y + 1,
                    m.rows,
                    1,
                    MAX_MAT_ROW,
                    is_real=False,
                )
                if ok:
                    m.rows = int(v)
                    i = min(i, m.rows)
                break
            if k == curses.KEY_F6:
                ok, v = input_number_inline(
                    scr,
                    MAT_X + MAT_OFS_RC + 1,
                    MAT_Y + 2,
                    m.cols,
                    1,
                    MAX_MAT_COL,
                    is_real=False,
                )
                if ok:
                    m.cols = int(v)
                    j = min(j, m.cols)
                break
            if (
                (10 <= k <= 13)
                or k in (9, curses.KEY_ENTER)
                or (32 <= k < 128 and chr(k) in "0123456789.- ")
            ):
                # start inline editing on cell (i, j)
                if 32 <= k < 128 and chr(k) in "0123456789.-":
                    initial_ch = chr(k)
                else:
                    initial_ch = None
                # compute on-screen coords
                left = MAT_X + (j - dt.x) * ELEM_SIZE_X + 1
                top = MAT_Y + (i - dt.y) + 1
                v = m.data[i - 1][j - 1]
                if initial_ch is not None:
                    # simulate pre-filling the edit buffer
                    buf_init = initial_ch
                    # render it, then normal inline edit
                    ok, val = _inline_edit(
                        scr, left, top, buf_init, MIN_MAT_VAL, MAX_MAT_VAL
                    )
                else:
                    ok, val = input_number_inline(
                        scr, left, top, v, MIN_MAT_VAL, MAX_MAT_VAL
                    )
                if ok:
                    m.data[i - 1][j - 1] = val
                    # auto-advance to next cell
                    j += 1
                    if j > m.cols:
                        j = 1
                        i = min(m.rows, i + 1)
                continue
        # confirmation
        if (
            message_box(
                scr,
                ["Матрица введена целиком", "Всё Вас устраивает?"],
                [("Да", "Y"), ("Нет", "N")],
            )
            == 1
        ):
            break


def _inline_edit(
    scr: Screen, x: int, y: int, buf: str, lo: float, hi: float
) -> tuple[bool, float]:
    """Variant of input_number_inline seeded with a partial buffer."""
    ptr = len(buf)
    curses.curs_set(1)
    while True:
        s = buf.ljust(MAX_INP_STR)[:MAX_INP_STR]
        scr.put_str(x, y, s, WHITE, BLUE)
        try:
            scr.win.move(y, x + min(ptr, MAX_INP_STR - 1))
        except curses.error:
            pass
        scr.refresh()
        k = scr.win.getch()
        if k == 27:
            curses.curs_set(0)
            return False, 0.0
        if k in (10, 13, curses.KEY_ENTER, 9):
            try:
                v = float(buf) if buf else 0.0
            except ValueError:
                curses.beep()
                continue
            if lo <= v <= hi:
                curses.curs_set(0)
                return True, v
            curses.beep()
            continue
        if k in (curses.KEY_BACKSPACE, 127, 8):
            if ptr > 0:
                ptr -= 1
                buf = buf[:ptr] + buf[ptr + 1 :]
            continue
        if 32 <= k < 128 and chr(k) in "0123456789.-":
            if len(buf) < MAX_INP_STR:
                buf = buf[:ptr] + chr(k) + buf[ptr:]
                ptr += 1


# ─── Operations ────────────────────────────────────────────────────────
def op_input(scr: Screen, a: Matrix, b: Matrix, delay_ms: int) -> None:
    i = message_box(
        scr,
        ["Какую матрицу будем редактировать?"],
        [("Матрица А", "A"), ("Матрица B", "B"), ("Отмена", "C")],
    )
    if i == 1:
        input_mat(scr, a, delay_ms)
    elif i == 2:
        input_mat(scr, b, delay_ms)


def op_check_equ(scr: Screen, a: Matrix, b: Matrix, delay_ms: int) -> None:
    clear_main_box(scr)
    dtA, dtB = ViewAttrs(), ViewAttrs()
    show_mat(scr, TWO_AX, TWO_AY, a, dtA)
    show_col_row(scr, TWO_AX, TWO_AY, a)
    show_mat(scr, TWO_BX, TWO_BY, b, dtB)
    show_col_row(scr, TWO_BX, TWO_BY, b)
    message_box(
        scr,
        [
            "При сравнении матриц сравниваются",
            "соответствующие элементы матриц,",
            "поэтому матрицы должны быть",
            "одинаковой размерности",
        ],
        [("ОК", "O")],
    )
    show_mat(scr, TWO_AX, TWO_AY, a, dtA)
    show_col_row(scr, TWO_AX, TWO_AY, a)
    show_mat(scr, TWO_BX, TWO_BY, b, dtB)
    show_col_row(scr, TWO_BX, TWO_BY, b)
    if a.cols != b.cols or a.rows != b.rows:
        curses.beep()
        message_box(
            scr, ["Матрицы не равны:", "разные размерности"], [("ОК", "O")]
        )
        return
    equ = True
    for i in range(1, a.rows + 1):
        for j in range(1, a.cols + 1):
            show_n_pos(scr, TWO_AX, TWO_AY, i, j, YELLOW, LGRAY, a, dtA)
            show_n_pos(scr, TWO_BX, TWO_BY, i, j, YELLOW, LGRAY, b, dtB)
            scr.refresh()
            sleep_ms(delay_ms)
            if a.data[i - 1][j - 1] != b.data[i - 1][j - 1]:
                show_n_pos(scr, TWO_AX, TWO_AY, i, j, RED, LGRAY, a, dtA)
                show_n_pos(scr, TWO_BX, TWO_BY, i, j, RED, LGRAY, b, dtB)
                equ = False
            sleep_ms(delay_ms)
    message_box(
        scr, ["Матрицы равны" if equ else "Матрицы не равны"], [("ОК", "O")]
    )


def op_add(scr: Screen, a: Matrix, b: Matrix, delay_ms: int) -> None:
    clear_main_box(scr)
    message_box(
        scr,
        [
            "При сложении матриц складываются",
            "соответствующие элементы матриц",
        ],
        [("ОК", "O")],
    )
    dtA, dtB, dtC = ViewAttrs(), ViewAttrs(), ViewAttrs()
    show_mat(scr, THR_AX, THR_AY, a, dtA)
    show_col_row(scr, THR_AX, THR_AY, a)
    show_mat(scr, THR_BX, THR_BY, b, dtB)
    show_col_row(scr, THR_BX, THR_BY, b)
    if a.rows != b.rows or a.cols != b.cols:
        curses.beep()
        message_box(
            scr,
            ["ОШИБКА", "Матрицы нельзя складывать:", "разные размерности"],
            [("ОК", "O")],
        )
        return
    new = Matrix(cols=a.cols, rows=a.rows)
    show_mat(scr, THR_CX, THR_CY, new, dtC)
    show_col_row(scr, THR_CX, THR_CY, new)
    for i in range(1, a.rows + 1):
        for j in range(1, a.cols + 1):
            new.data[i - 1][j - 1] = a.data[i - 1][j - 1] + b.data[i - 1][j - 1]
            show_n_pos(scr, THR_AX, THR_AY, i, j, YELLOW, LGRAY, a, dtA)
            show_n_pos(scr, THR_BX, THR_BY, i, j, YELLOW, LGRAY, b, dtB)
            show_n_pos(scr, THR_CX, THR_CY, i, j, YELLOW, LGRAY, new, dtC)
            scr.refresh()
            sleep_ms(delay_ms)
            show_n_pos(scr, THR_AX, THR_AY, i, j, RED, LGRAY, a, dtA)
            show_n_pos(scr, THR_BX, THR_BY, i, j, RED, LGRAY, b, dtB)
            show_n_pos(scr, THR_CX, THR_CY, i, j, RED, LGRAY, new, dtC)
            scr.refresh()
            sleep_ms(delay_ms)


def op_mult_number(scr: Screen, a: Matrix, delay_ms: int) -> None:
    clear_main_box(scr)
    message_box(
        scr,
        [
            "При умножении матрицы на число",
            "исходная матрица поэлементно умножается",
            "на это число",
        ],
        [("ОК", "O")],
    )
    dt = ViewAttrs()
    show_mat(scr, TWO_AX, TWO_AY, a, dt)
    show_col_row(scr, TWO_AX, TWO_AY, a)
    ok, n = input_number_prompt(
        scr, "Введите число для умножения:", 1.0, MIN_MAT_VAL, MAX_MAT_VAL
    )
    if not ok:
        return
    for i in range(1, a.rows + 1):
        for j in range(1, a.cols + 1):
            show_n_pos(scr, TWO_AX, TWO_AY, i, j, YELLOW, LGRAY, a, dt)
            scr.refresh()
            sleep_ms(delay_ms)
            a.data[i - 1][j - 1] *= n
            show_n_pos(scr, TWO_AX, TWO_AY, i, j, BROWN, LGRAY, a, dt)
            scr.refresh()
            sleep_ms(delay_ms)


def op_mult_mats(scr: Screen, a: Matrix, b: Matrix, delay_ms: int) -> None:
    clear_main_box(scr)
    message_box(
        scr,
        [
            "При умножении матриц строка первой",
            "умножается на столбец второй,",
            "результаты суммируются.",
        ],
        [("ОК", "O")],
    )
    dtA, dtB, dtC = ViewAttrs(), ViewAttrs(), ViewAttrs()
    show_mat(scr, THR_AX, THR_AY, a, dtA)
    show_col_row(scr, THR_AX, THR_AY, a)
    show_mat(scr, THR_BX, THR_BY, b, dtB)
    show_col_row(scr, THR_BX, THR_BY, b)
    if a.cols != b.rows:
        curses.beep()
        message_box(
            scr,
            ["ОШИБКА", "Матрицы нельзя умножать:", "A.cols ≠ B.rows"],
            [("ОК", "O")],
        )
        return
    new = Matrix(rows=a.rows, cols=b.cols)
    show_mat(scr, THR_CX, THR_CY, new, dtC)
    show_col_row(scr, THR_CX, THR_CY, new)
    for i in range(1, a.rows + 1):
        for j in range(1, b.cols + 1):
            s = 0.0
            for k in range(1, a.cols + 1):
                s += a.data[i - 1][k - 1] * b.data[k - 1][j - 1]
                show_n_pos(scr, THR_AX, THR_AY, i, k, YELLOW, LGRAY, a, dtA)
                show_n_pos(scr, THR_BX, THR_BY, k, j, YELLOW, LGRAY, b, dtB)
                scr.refresh()
                sleep_ms(delay_ms)
            for k in range(1, a.cols + 1):
                dtA.at[i - 1][k - 1] = (LGRAY, BLUE)
                dtB.at[k - 1][j - 1] = (LGRAY, BLUE)
            new.data[i - 1][j - 1] = s
            show_n_pos(scr, THR_CX, THR_CY, i, j, RED, LGRAY, new, dtC)
            scr.refresh()
            sleep_ms(delay_ms)
    # copy result back into A
    a.rows, a.cols = new.rows, new.cols
    for i in range(a.rows):
        for j in range(a.cols):
            a.data[i][j] = new.data[i][j]


def op_transpose(scr: Screen, a: Matrix, delay_ms: int) -> None:
    clear_main_box(scr)
    dtA, dtB = ViewAttrs(), ViewAttrs()
    new = Matrix(rows=a.cols, cols=a.rows)
    show_mat(scr, TWO_AX, TWO_AY, a, dtA)
    show_col_row(scr, TWO_AX, TWO_AY, a)
    show_mat(scr, TWO_BX, TWO_BY, new, dtB)
    show_col_row(scr, TWO_BX, TWO_BY, new)
    message_box(
        scr,
        [
            "При транспонировании строки становятся",
            "столбцами, столбцы — строками.",
        ],
        [("ОК", "O")],
    )
    show_mat(scr, TWO_AX, TWO_AY, a, dtA)
    show_col_row(scr, TWO_AX, TWO_AY, a)
    show_mat(scr, TWO_BX, TWO_BY, new, dtB)
    show_col_row(scr, TWO_BX, TWO_BY, new)
    for i in range(1, a.rows + 1):
        for j in range(1, a.cols + 1):
            new.data[j - 1][i - 1] = a.data[i - 1][j - 1]
            show_n_pos(scr, TWO_AX, TWO_AY, i, j, YELLOW, LGRAY, a, dtA)
            show_n_pos(scr, TWO_BX, TWO_BY, j, i, YELLOW, LGRAY, new, dtB)
            scr.refresh()
            sleep_ms(delay_ms)
    a.rows, a.cols = new.rows, new.cols
    for i in range(a.rows):
        for j in range(a.cols):
            a.data[i][j] = new.data[i][j]
    local_msg(scr, "Матрица транспонирована")


# ─ Determinant (Gaussian elimination) ─────────────────────────────────
def determinant(m: Matrix) -> float:
    n = m.cols
    a = [[m.data[i][j] for j in range(n)] for i in range(n)]
    det, sign = 1.0, 1.0
    for k in range(n - 1):
        # partial pivot on column k below diagonal
        piv = k
        mx = abs(a[k][k])
        for r in range(k + 1, n):
            if abs(a[r][k]) > mx:
                mx = abs(a[r][k])
                piv = r
        if mx == 0:
            return 0.0
        if piv != k:
            a[k], a[piv] = a[piv], a[k]
            sign = -sign
        for r in range(k + 1, n):
            g = a[r][k] / a[k][k]
            for c in range(k, n):
                a[r][c] -= g * a[k][c]
    for i in range(n):
        det *= a[i][i]
    return det * sign


# ─── Identification operations ─────────────────────────────────────────
def _animate_mat(
    scr: Screen,
    a: Matrix,
    delay_ms: int,
    predicate: Callable[[int, int, float], str | None],
) -> bool:
    """Walk the matrix; predicate returns None/OK or a colour name for error.
    Returns True if no errors were flagged."""
    dt = ViewAttrs()
    show_mat(scr, IDN_X, IDN_Y, a, dt)
    show_col_row(scr, IDN_X, IDN_Y, a)
    ok = True
    for i in range(1, a.rows + 1):
        for j in range(1, a.cols + 1):
            show_n_pos(scr, IDN_X, IDN_Y, i, j, YELLOW, LGRAY, a, dt)
            scr.refresh()
            sleep_ms(delay_ms)
            res = predicate(i, j, a.data[i - 1][j - 1])
            if res == "err":
                show_n_pos(scr, IDN_X, IDN_Y, i, j, RED, LGRAY, a, dt)
                ok = False
            elif res == "ok":
                show_n_pos(scr, IDN_X, IDN_Y, i, j, GREEN, LGRAY, a, dt)
            scr.refresh()
            sleep_ms(delay_ms)
    return ok


def id_null(scr: Screen, a: Matrix, delay_ms: int) -> None:
    local_msg(scr, "Тестирую Нуль-матрицу ...")
    ok = _animate_mat(
        scr, a, delay_ms, lambda i, j, v: "err" if v != 0 else None
    )
    if ok:
        message_box(
            scr, ["Это Нуль-матрица", "все элементы равны нулю"], [("ОК", "O")]
        )
    else:
        message_box(
            scr,
            ["Это не Нуль-матрица", "не все элементы равны нулю"],
            [("ОК", "O")],
        )


def _require_square(scr: Screen, a: Matrix, kind: str) -> bool:
    if a.rows == a.cols:
        return True
    curses.beep()
    message_box(
        scr,
        ["ОШИБКА", f"Эта матрица не {kind},", "так как она не квадратная"],
        [("ОК", "O")],
    )
    return False


def id_diag(scr: Screen, a: Matrix, delay_ms: int) -> None:
    local_msg(scr, "Тестирую диагональную матрицу ...")
    if not _require_square(scr, a, "диагональная"):
        return

    def p(i, j, v):
        if i == j:
            return "ok"
        return "err" if v != 0 else None

    ok = _animate_mat(scr, a, delay_ms, p)
    message_box(
        scr,
        (
            ["Это диагональная матрица"]
            if ok
            else ["Это не диагональная матрица"]
        ),
        [("ОК", "O")],
    )


def id_identity(scr: Screen, a: Matrix, delay_ms: int) -> None:
    local_msg(scr, "Тестирую единичную матрицу ...")
    if not _require_square(scr, a, "единичная"):
        return

    def p(i, j, v):
        if i == j:
            return "ok" if v == 1 else "err"
        return "err" if v != 0 else None

    ok = _animate_mat(scr, a, delay_ms, p)
    message_box(
        scr,
        ["Это единичная матрица"] if ok else ["Это не единичная матрица"],
        [("ОК", "O")],
    )


def id_symm(scr: Screen, a: Matrix, delay_ms: int, sign: int) -> None:
    kind = "симметрическая" if sign == 1 else "кососимметрическая"
    local_msg(scr, f"Тестирую {kind} матрицу ...")
    if not _require_square(scr, a, kind):
        return
    dt = ViewAttrs()
    show_mat(scr, IDN_X, IDN_Y, a, dt)
    show_col_row(scr, IDN_X, IDN_Y, a)
    ok = True
    for i in range(2, a.rows + 1):
        for j in range(1, i):
            show_n_pos(scr, IDN_X, IDN_Y, i, j, YELLOW, LGRAY, a, dt)
            show_n_pos(scr, IDN_X, IDN_Y, j, i, YELLOW, LGRAY, a, dt)
            scr.refresh()
            sleep_ms(delay_ms)
            if a.data[i - 1][j - 1] != a.data[j - 1][i - 1] * sign:
                show_n_pos(scr, IDN_X, IDN_Y, i, j, RED, LGRAY, a, dt)
                show_n_pos(scr, IDN_X, IDN_Y, j, i, RED, LGRAY, a, dt)
                ok = False
            scr.refresh()
            sleep_ms(delay_ms)
    message_box(
        scr,
        [f"Это {kind} матрица"] if ok else [f"Это не {kind} матрица"],
        [("ОК", "O")],
    )


def id_triangular(scr: Screen, a: Matrix, delay_ms: int) -> None:
    local_msg(scr, "Тестирую треугольную матрицу ...")
    if not _require_square(scr, a, "треугольная"):
        return
    dt = ViewAttrs()
    show_mat(scr, IDN_X, IDN_Y, a, dt)
    show_col_row(scr, IDN_X, IDN_Y, a)
    ok = True
    for i in range(2, a.rows + 1):
        for j in range(1, i):
            show_n_pos(scr, IDN_X, IDN_Y, i, j, YELLOW, LGRAY, a, dt)
            scr.refresh()
            sleep_ms(delay_ms)
            if a.data[i - 1][j - 1] != 0:
                show_n_pos(scr, IDN_X, IDN_Y, i, j, RED, LGRAY, a, dt)
                ok = False
            scr.refresh()
            sleep_ms(delay_ms)
    message_box(
        scr,
        ["Это треугольная матрица"] if ok else ["Это не треугольная матрица"],
        [("ОК", "O")],
    )


def id_degen(scr: Screen, a: Matrix, delay_ms: int) -> None:
    clear_main_box(scr)
    dt = ViewAttrs()
    show_mat(scr, IDN_X, IDN_Y, a, dt)
    show_col_row(scr, IDN_X, IDN_Y, a)
    local_msg(scr, "Тестирую определитель ...")
    if a.rows != a.cols:
        curses.beep()
        message_box(
            scr,
            ["Это вырожденная матрица:", "не квадратная — определитель = 0"],
            [("ОК", "O")],
        )
        return
    d = determinant(a)
    if d == 0:
        message_box(
            scr,
            ["Это вырожденная матрица", "Определитель равен нулю"],
            [("ОК", "O")],
        )
    else:
        message_box(
            scr,
            ["Это невырожденная матрица", f"Определитель = {d:.3f}"],
            [("ОК", "O")],
        )


def op_ident(scr: Screen, a: Matrix, delay_ms: int) -> None:
    clear_main_box(scr)
    # hide sidebar (DOS original does so)
    scr.fill(1, 1, MAIN_BACK_X - 2, SCR_H - 2, " ", LBLUE, LBLUE)
    dt = ViewAttrs()
    show_mat(scr, IDN_X, IDN_Y, a, dt)
    show_col_row(scr, IDN_X, IDN_Y, a)
    ops = [
        id_null,
        id_diag,
        id_identity,
        lambda s, m, d: id_symm(s, m, d, 1),
        lambda s, m, d: id_symm(s, m, d, -1),
        id_triangular,
        id_degen,
    ]
    while True:
        # sub-menu in sidebar style
        selected = 0
        while True:
            draw_sidebar(scr, CHECK_BUTTONS, selected)
            scr.refresh()
            k = scr.win.getch()
            if k == curses.KEY_UP:
                selected = (selected - 1) % len(CHECK_BUTTONS)
            elif k == curses.KEY_DOWN:
                selected = (selected + 1) % len(CHECK_BUTTONS)
            elif k in (10, 13, curses.KEY_ENTER):
                break
            elif k == 27:
                selected = len(CHECK_BUTTONS) - 1
                break
            elif 32 <= k < 256:
                ch = chr(k).lower()
                hit = [
                    i
                    for i, (_, h) in enumerate(CHECK_BUTTONS)
                    if h.lower() == ch
                ]
                if hit:
                    selected = hit[0]
                    break
        if selected == len(CHECK_BUTTONS) - 1:
            break
        # wipe working area except sidebar hidden
        clear_main_box(scr)
        show_mat(scr, IDN_X, IDN_Y, a, dt)
        show_col_row(scr, IDN_X, IDN_Y, a)
        ops[selected](scr, a, delay_ms)
        # Dialog shadow may have clipped the sidebar frame & fill — repaint.
        scr.fill(0, 0, MAIN_BACK_X - 1, SCR_H - 1, " ", LBLUE, LBLUE)
        scr.box(0, 0, MAIN_BACK_X - 1, SCR_H - 1, WHITE, LBLUE)
        clear_main_box(scr)
        show_mat(scr, IDN_X, IDN_Y, a, dt)
        show_col_row(scr, IDN_X, IDN_Y, a)


# ─── Main loop ─────────────────────────────────────────────────────────
def app(stdscr: "curses._CursesWindow") -> None:
    # Guard against tiny windows
    H, W = stdscr.getmaxyx()
    if H < SCR_H or W < SCR_W:
        stdscr.addstr(0, 0, f"Need at least {SCR_W}x{SCR_H}, have {W}x{H}")
        stdscr.addstr(1, 0, "Press any key to exit.")
        stdscr.getch()
        return
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(-1)
    PAL.setup()
    scr = Screen(stdscr)

    a = Matrix()
    b = Matrix()
    delay_ms = 100
    draw_background(scr)

    selected = 0
    while True:
        draw_sidebar(scr, MAIN_BUTTONS, selected)
        scr.refresh()
        k = scr.win.getch()
        if k == curses.KEY_UP:
            selected = (selected - 1) % len(MAIN_BUTTONS)
            continue
        if k == curses.KEY_DOWN:
            selected = (selected + 1) % len(MAIN_BUTTONS)
            continue
        cmd: int | None = None
        if k in (10, 13, curses.KEY_ENTER):
            cmd = selected + 1
        elif k == 27:
            cmd = CM_EXIT
        elif 32 <= k < 256:
            ch = chr(k).lower()
            for i, (_t, h) in enumerate(MAIN_BUTTONS):
                if h.lower() == ch:
                    cmd = i + 1
                    selected = i
                    break
        if cmd is None:
            continue

        if cmd == CM_INPUT:
            op_input(scr, a, b, delay_ms)
        elif cmd == CM_EQU:
            op_check_equ(scr, a, b, delay_ms)
        elif cmd == CM_ADD:
            op_add(scr, a, b, delay_ms)
        elif cmd == CM_MULTN:
            op_mult_number(scr, a, delay_ms)
        elif cmd == CM_MULTM:
            op_mult_mats(scr, a, b, delay_ms)
        elif cmd == CM_TRANS:
            op_transpose(scr, a, delay_ms)
        elif cmd == CM_IDENT:
            op_ident(scr, a, delay_ms)
        elif cmd == CM_DELAY:
            clear_main_box(scr)
            ok, v = input_number_prompt(
                scr,
                "Введите задержку (мс):",
                float(delay_ms),
                DELAY_MIN,
                DELAY_MAX,
                is_real=False,
            )
            if ok:
                delay_ms = int(v)
        elif cmd == CM_ABOUT:
            message_box(scr, ABOUT_LINES, [("ОК", "O")])
        elif cmd == CM_EXIT:
            if (
                message_box(
                    scr,
                    ["Хотите выйти из программы?"],
                    [("Да", "Y"), ("Нет", "N"), ("Отмена", "C")],
                )
                == 1
            ):
                return
        # Repaint the whole backdrop: dialogs/windows may have overdrawn the
        # sidebar frame column, the top bar, or the shadow strip to its right.
        draw_background(scr)


def main() -> None:
    try:
        curses.wrapper(app)
    finally:
        print(
            "■ Matrix 2.0 (Python/curses port) "
            "— Alexander Demin, 1995 / 2026 ■"
        )


if __name__ == "__main__":
    main()
