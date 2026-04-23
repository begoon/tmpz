#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pygame-ce>=2.5"]
# ///
"""
Matrix v1.0 — Python/SDL port of the 1995 Turbo Pascal BGI demo
by Alexander Demin (MAI, Dept. 302).

Original: Turbo Pascal 5.5 + BGI, 640x480 VGA, mouse + keyboard.
This port uses pygame-ce (SDL2) at 2x logical scale.

Run:  uv run matrix1.py
"""

from __future__ import annotations

import random
import sys
from typing import Callable, Optional

import pygame

# ------------------------------------------------------------------ scale
SCALE = 2
LW, LH = 640, 480
W, H = LW * SCALE, LH * SCALE
FPS = 60


def s(v: float) -> int:
    return int(v * SCALE)


# --------------------------------------------------------------- palette (VGA)
BLACK = (0, 0, 0)
BLUE = (0, 0, 170)
GREEN = (0, 170, 0)
CYAN = (0, 170, 170)
RED = (170, 0, 0)
LIGHT_GRAY = (170, 170, 170)
DARK_GRAY = (85, 85, 85)
LIGHT_BLUE = (85, 85, 255)
YELLOW = (255, 255, 85)
WHITE = (252, 252, 252)

# --------------------------------------------------------- layout (COMMON.PAS)
SYM_W, SYM_H = 8, 8
ADD_X, ADD_Y = 5, 7
DELTA_X, DELTA_Y = 10, 10
FULL_H = SYM_H + ADD_Y * 2 + DELTA_Y
START_X = 10

MAIN_BACK_X = 186
MAIN_BACK_Y = 12
MAX_COL = 10
MAX_ROW = 10
MAX_VAL = 9.9
MIN_VAL = -9.9

MAT_X = MAIN_BACK_X + 30 + ADD_X
MAT_Y = 120
COL_ROW_X = MAIN_BACK_X + 30
COL_ROW_Y = MAIN_BACK_Y + 10
COL_ROW_SZX = LW - MAIN_BACK_X - 60
COL_ROW_SZY = 2 * SYM_H + ADD_Y * 4

REP_X = MAT_X
REP_Y = MAT_Y + MAX_ROW * 20 + 20
REP_SZX = LW - MAIN_BACK_X - 60
REP_SZY = SYM_H + ADD_X * 2

# -------------------------------------------------------------- text resources
TITLE = "*  Matrix  Version 1.0  *"

MAIN_BUTTONS = [
    "~В~вод",
    "~З~аполнение",
    "~Р~авенство",
    "~C~ложение",
    "~У~множение на число",
    "У~м~ножение матpиц",
    "~Т~pанспониpование",
    "~И~дентификация",
    "~О~ пpогpамме",
    "В~ы~ход",
]

OK_BUTS = ["~Д~а"]
YESNO_BUTS = ["~Д~а", "~Н~ет", "~О~тмена"]
MAT_BUTS = ["Матpица ~А~", "Матpица ~В~", "~О~тмена"]
WHAT_BUTS = [
    "~Ч~ислом",
    "~C~лyчайным обpазом",
    "~О~тмена",
]
CHECK_BUTS = [
    "~Н~yль-матpица",
    "~Д~иагональная",
    "~Е~диничная",
    "~C~имметpическая",
    "~К~ососиметpическая",
    "~Т~pеyгольная",
    "~В~ыpожденная",
    "В~о~звpат в меню",
]

ABOUT_MSG = [
    "Matrix",
    "Демонстpационная пpогpамма",
    "pаботы с матpицами",
    "Веpсия 1.0",
    "Автоp: Александp Демин",
    "МАИ, Кафедpа 302, 1995",
]
EXIT_MSG = ["Хотите выйти из пpогpаммы ?"]

# ================================================================= pygame init
pygame.init()
pygame.display.set_caption("Matrix v1.0 — Alexander Demin, 1995 (SDL port)")
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

# Scale the font so 8x8 logical glyph cell ≈ 16x16 on screen.
FONT = pygame.font.SysFont(
    "menlo,consolas,dejavusansmono,courier,monospace", s(7) + 2, bold=True
)
FONT_MONO_W = FONT.size("0")[0]
FONT_H = FONT.get_linesize()


# =============================================================== event helpers
def poll_quit(events: list[pygame.event.Event]) -> None:
    for e in events:
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)


def wait(ms: int) -> None:
    end = pygame.time.get_ticks() + ms
    while pygame.time.get_ticks() < end:
        events = pygame.event.get()
        poll_quit(events)
        pygame.display.flip()
        clock.tick(FPS)


# ========================================================== drawing primitives
def fill(color, x, y, w, h):
    pygame.draw.rect(screen, color, (s(x), s(y), s(w), s(h)))


def draw_box(x1, y1, x2, y2, pressed: bool, color):
    light = WHITE if pressed else BLACK
    dark = BLACK if pressed else WHITE
    fill(color, x1 + 2, y1 + 2, x2 - x1 - 3, y2 - y1 - 3)
    # top + left
    pygame.draw.line(screen, light, (s(x1), s(y1)), (s(x2), s(y1)), SCALE)
    pygame.draw.line(
        screen, light, (s(x1 + 1), s(y1 + 1)), (s(x2 - 1), s(y1 + 1)), SCALE
    )
    pygame.draw.line(screen, light, (s(x1), s(y1)), (s(x1), s(y2)), SCALE)
    pygame.draw.line(
        screen, light, (s(x1 + 1), s(y1 + 1)), (s(x1 + 1), s(y2 - 1)), SCALE
    )
    # bottom + right
    pygame.draw.line(screen, dark, (s(x2), s(y1)), (s(x2), s(y2)), SCALE)
    pygame.draw.line(
        screen, dark, (s(x2 - 1), s(y1 + 1)), (s(x2 - 1), s(y2 - 1)), SCALE
    )
    pygame.draw.line(screen, dark, (s(x1), s(y2)), (s(x2), s(y2)), SCALE)
    pygame.draw.line(
        screen, dark, (s(x1 + 1), s(y2 - 1)), (s(x2 - 1), s(y2 - 1)), SCALE
    )


def parse_hot(text: str) -> tuple[str, set[int]]:
    out: list[str] = []
    hot: set[int] = set()
    inside = False
    for ch in text:
        if ch == "~":
            inside = not inside
            continue
        if inside:
            hot.add(len(out))
        out.append(ch)
    return "".join(out), hot


def render_hot(text: str, hot_color, tx_color) -> pygame.Surface:
    clean, hot = parse_hot(text)
    surfs = [
        FONT.render(ch, True, hot_color if i in hot else tx_color)
        for i, ch in enumerate(clean)
    ]
    if not surfs:
        return pygame.Surface((0, 0), pygame.SRCALPHA)
    width = sum(sf.get_width() for sf in surfs)
    height = max(sf.get_height() for sf in surfs)
    out = pygame.Surface((width, height), pygame.SRCALPHA)
    x = 0
    for sf in surfs:
        out.blit(sf, (x, 0))
        x += sf.get_width()
    return out


def draw_text(
    x: int, y: int, text: str, color, *, center: bool = False
) -> None:
    surf = FONT.render(text, True, color)
    sx = s(x) - (surf.get_width() // 2 if center else 0)
    screen.blit(surf, (sx, s(y)))


def draw_text_hot(
    x: int, y: int, text: str, hot_color, tx_color, *, center: bool = False
) -> None:
    surf = render_hot(text, hot_color, tx_color)
    sx = s(x) - (surf.get_width() // 2 if center else 0)
    screen.blit(surf, (sx, s(y)))


def draw_button(
    x1, y1, x2, y2, text: str, pressed: bool, bg, hot_color, tx_color
) -> None:
    draw_box(x1, y1, x2, y2, not pressed, bg)
    surf = render_hot(text, hot_color, tx_color)
    cx = s((x1 + x2) // 2) - surf.get_width() // 2
    cy = s((y1 + y2) // 2) - surf.get_height() // 2
    if pressed:
        cx += s(1)
        cy += s(1)
    screen.blit(surf, (cx, cy))


# ========================================================== screen backgrounds
def draw_background() -> None:
    screen.fill(BLACK)
    # left blue panel
    pygame.draw.rect(screen, LIGHT_BLUE, (0, 0, s(MAIN_BACK_X), H))
    # main dark-gray area
    pygame.draw.rect(
        screen,
        DARK_GRAY,
        (
            s(MAIN_BACK_X),
            s(MAIN_BACK_Y),
            W - s(MAIN_BACK_X),
            H - s(MAIN_BACK_Y),
        ),
    )
    # title bar
    draw_box(MAIN_BACK_X, 0, LW - 1, MAIN_BACK_Y - 1, True, RED)
    ts = render_hot(TITLE, YELLOW, WHITE)
    screen.blit(
        ts,
        (
            s(MAIN_BACK_X) + (W - s(MAIN_BACK_X)) // 2 - ts.get_width() // 2,
            s(0) + (s(MAIN_BACK_Y) - ts.get_height()) // 2,
        ),
    )


def clear_work() -> None:
    """Clear the right-hand work area (used between screens)."""
    pygame.draw.rect(
        screen,
        DARK_GRAY,
        (
            s(MAIN_BACK_X),
            s(MAIN_BACK_Y),
            W - s(MAIN_BACK_X),
            H - s(MAIN_BACK_Y),
        ),
    )


# ================================================================ matrix state
matrix_a: list[list[float]] = [[0.0] * MAX_COL for _ in range(MAX_ROW)]
matrix_b: list[list[float]] = [[0.0] * MAX_COL for _ in range(MAX_ROW)]
mat_a_col = MAX_COL
mat_a_row = MAX_ROW
mat_b_col = MAX_COL
mat_b_row = MAX_ROW


def fmt_cell(n: float) -> str:
    txt = f"{n:4.1f}"
    return txt[:4]


# ============================================================== matrix drawing
CELL_W = 5 * SYM_W  # 40 logical px per cell (4 digits + pad)
CELL_H = 2 * SYM_H  # 16 logical px per row


def show_cell(left: int, top: int, color, i: int, j: int, value: float) -> None:
    x = left + (j - 1) * CELL_W
    y = top + (i - 1) * CELL_H
    pygame.draw.rect(
        screen, LIGHT_GRAY, (s(x), s(y), s(4 * SYM_W + 2), s(SYM_H + 2))
    )
    draw_text(x, y - 2, fmt_cell(value), color)


def show_mat(
    x: int, y: int, mat: list[list[float]], col: int, row: int
) -> None:
    sizex = col * CELL_W + ADD_X * 2
    sizey = row * CELL_H + ADD_Y
    draw_box(x - ADD_X, y - ADD_Y, x + sizex, y + sizey, True, LIGHT_GRAY)
    for i in range(1, row + 1):
        for j in range(1, col + 1):
            show_cell(x, y, BLUE, i, j, mat[i - 1][j - 1])


# ============================================================== text input box
def text_input_modal(
    prompt: str, initial: str, max_len: int, allow_signed: bool
) -> Optional[str]:
    """Simple centered text-input modal for numbers. Returns None on Esc."""
    backup = screen.copy()
    box_w = max(260, len(prompt) * FONT_MONO_W // SCALE + 60)
    box_h = 70
    bx = (LW - box_w) // 2
    by = (LH - box_h) // 2
    buf = list(initial)
    cursor = len(buf)

    while True:
        screen.blit(backup, (0, 0))
        draw_box(bx, by, bx + box_w, by + box_h, True, RED)
        draw_text(bx + 14, by + 12, prompt, WHITE)
        # input line
        fld_x = bx + 14
        fld_y = by + 36
        fld_w = box_w - 28
        pygame.draw.rect(
            screen, WHITE, (s(fld_x), s(fld_y), s(fld_w), s(SYM_H + 4))
        )
        text = "".join(buf)
        surf = FONT.render(text, True, BLACK)
        screen.blit(surf, (s(fld_x + 2), s(fld_y)))
        # blinking cursor
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            cx = s(fld_x + 2) + FONT.size(text[:cursor])[0]
            pygame.draw.rect(screen, BLACK, (cx, s(fld_y), SCALE, s(SYM_H + 2)))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    return "".join(buf)
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key == pygame.K_BACKSPACE:
                    if cursor > 0:
                        del buf[cursor - 1]
                        cursor -= 1
                    continue
                if e.key == pygame.K_LEFT:
                    cursor = max(0, cursor - 1)
                    continue
                if e.key == pygame.K_RIGHT:
                    cursor = min(len(buf), cursor + 1)
                    continue
            if e.type == pygame.TEXTINPUT:
                for ch in e.text:
                    if len(buf) >= max_len:
                        break
                    if (
                        ch.isdigit()
                        or ch == "."
                        or (allow_signed and ch == "-")
                    ):
                        buf.insert(cursor, ch)
                        cursor += 1
        clock.tick(FPS)


def input_number(
    prompt: str, default: float, lo: float, hi: float, integer: bool
) -> Optional[float]:
    init = f"{int(default)}" if integer else f"{default:g}"
    while True:
        raw = text_input_modal(
            prompt, init, 5 if integer else 6, allow_signed=True
        )
        if raw is None:
            return None
        try:
            n = float(raw)
        except ValueError:
            message_box(
                ["ОШИБКА", "Hедопyстимые символы в числе", "Повтоpите ввод"],
                OK_BUTS,
            )
            continue
        if integer:
            n = int(n)
        if n < lo or n > hi:
            message_box(
                [
                    "ОШИБКА",
                    "Введенное число не лежит",
                    "в pазpешенных пpеделах",
                    "Повтоpите ввод",
                ],
                OK_BUTS,
            )
            continue
        return float(n)


# ================================================================= message box
def _menu_buttons_geometry(
    n: int, labels: list[str], y: int
) -> list[tuple[int, int, int, int]]:
    max_len = max(len(parse_hot(t)[0]) for t in labels)
    bw = max_len * SYM_W + ADD_X * 2 + DELTA_X
    bh = SYM_H + ADD_Y * 2
    total = bw * n
    left0 = (LW - total) // 2
    return [
        (left0 + i * bw, y, left0 + i * bw + bw - DELTA_X + 2, y + bh)
        for i in range(n)
    ]


def message_box(lines: list[str], buttons: list[str]) -> int:
    """Modal message box. Returns 1-based button index, 0 on Esc."""
    backup = screen.copy()

    # size
    max_len = max((len(ln) for ln in lines), default=0)
    text_w = (max_len + 4) * SYM_W + ADD_X * 2
    # button width
    but_max = max(len(parse_hot(b)[0]) for b in buttons)
    bw = but_max * SYM_W + ADD_X * 2 + DELTA_X
    buts_w = bw * len(buttons) + 20
    size_x = max(text_w, buts_w, 300)
    size_y = (
        (len(lines) + 2) * (SYM_H * 2) + (SYM_H + ADD_Y * 2) + ADD_Y * 2 + 30
    )
    left = (LW - size_x) // 2
    top = (LH - size_y) // 2
    right = left + size_x
    bottom = top + size_y

    selected = 0

    def draw(
        active: int, pressed_idx: int = -1
    ) -> list[tuple[int, int, int, int]]:
        screen.blit(backup, (0, 0))
        draw_box(left, top, right, bottom, True, RED)
        for i, ln in enumerate(lines):
            surf = FONT.render(ln, True, WHITE)
            screen.blit(
                surf,
                (
                    s(left + size_x // 2) - surf.get_width() // 2,
                    s(top + SYM_H * 2 * (i + 1) + ADD_Y),
                ),
            )
        by = top + SYM_H * 2 * (len(lines) + 2) + ADD_Y
        rects = _menu_buttons_geometry(len(buttons), buttons, by)
        for i, (x1, y1, x2, y2) in enumerate(rects):
            bg = DARK_GRAY if i == active else BLUE
            pressed = i == pressed_idx
            draw_button(x1, y1, x2, y2, buttons[i], pressed, bg, WHITE, GREEN)
        pygame.display.flip()
        return rects

    rects = draw(selected)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    screen.blit(backup, (0, 0))
                    return 0
                if e.key == pygame.K_RETURN:
                    rects = draw(selected, selected)
                    wait(80)
                    screen.blit(backup, (0, 0))
                    return selected + 1
                if e.key in (pygame.K_TAB, pygame.K_RIGHT, pygame.K_DOWN):
                    selected = (selected + 1) % len(buttons)
                    rects = draw(selected)
                if e.key in (pygame.K_LEFT, pygame.K_UP):
                    selected = (selected - 1) % len(buttons)
                    rects = draw(selected)
                if e.key >= pygame.K_1 and e.key <= pygame.K_9:
                    idx = e.key - pygame.K_1
                    if idx < len(buttons):
                        rects = draw(idx, idx)
                        wait(80)
                        screen.blit(backup, (0, 0))
                        return idx + 1
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                for i, (x1, y1, x2, y2) in enumerate(rects):
                    if s(x1) <= mx <= s(x2) and s(y1) <= my <= s(y2):
                        rects = draw(i, i)
                        wait(80)
                        screen.blit(backup, (0, 0))
                        return i + 1
            if e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                for i, (x1, y1, x2, y2) in enumerate(rects):
                    if s(x1) <= mx <= s(x2) and s(y1) <= my <= s(y2):
                        if i != selected:
                            selected = i
                            rects = draw(selected)
                        break
        clock.tick(FPS)


# ============================================================ local status msg
def local_msg(text: str, wait_key: bool = False) -> None:
    draw_button(
        REP_X,
        REP_Y,
        REP_X + REP_SZX,
        REP_Y + REP_SZY,
        text,
        False,
        CYAN,
        BLACK,
        BLACK,
    )
    pygame.display.flip()
    if wait_key:
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if e.type == pygame.KEYDOWN and e.key in (
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                    pygame.K_ESCAPE,
                ):
                    return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    return
            clock.tick(FPS)


# ========================================================== main vertical menu
BTN_W = MAIN_BACK_X - 2 * START_X
BTN_H = SYM_H + ADD_Y * 2


def main_menu_rects() -> list[tuple[int, int, int, int]]:
    n = len(MAIN_BUTTONS)
    start_y = (LH - (BTN_H + DELTA_Y) * n) // 2
    return [
        (
            START_X,
            start_y + (BTN_H + DELTA_Y) * i,
            START_X + BTN_W,
            start_y + (BTN_H + DELTA_Y) * i + BTN_H,
        )
        for i in range(n)
    ]


def draw_main_menu(selected: int, pressed: int = -1) -> None:
    rects = main_menu_rects()
    # clear left column
    pygame.draw.rect(
        screen,
        LIGHT_BLUE,
        (0, s(MAIN_BACK_Y), s(MAIN_BACK_X), H - s(MAIN_BACK_Y)),
    )
    for i, (x1, y1, x2, y2) in enumerate(rects):
        bg = DARK_GRAY if i == selected else BLUE
        draw_button(
            x1, y1, x2, y2, MAIN_BUTTONS[i], i == pressed, bg, WHITE, GREEN
        )


def sidebar_menu(buttons: list[str]) -> int:
    """Vertical sidebar menu, like MESSAGE.PAS :: Menu(False, ...)."""
    n = len(buttons)
    bh = SYM_H + ADD_Y * 2
    start_y = (LH - (bh + DELTA_Y) * n) // 2
    rects = [
        (
            START_X,
            start_y + (bh + DELTA_Y) * i,
            START_X + BTN_W,
            start_y + (bh + DELTA_Y) * i + bh,
        )
        for i in range(n)
    ]
    selected = 0

    def draw(active: int, pressed_idx: int = -1) -> None:
        pygame.draw.rect(
            screen,
            LIGHT_BLUE,
            (0, s(MAIN_BACK_Y), s(MAIN_BACK_X), H - s(MAIN_BACK_Y)),
        )
        for i, (x1, y1, x2, y2) in enumerate(rects):
            bg = DARK_GRAY if i == active else BLUE
            pressed = i == pressed_idx
            draw_button(x1, y1, x2, y2, buttons[i], pressed, bg, WHITE, GREEN)
        pygame.display.flip()

    draw(selected)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return 0
                if e.key == pygame.K_RETURN:
                    draw(selected, selected)
                    wait(80)
                    return selected + 1
                if e.key in (pygame.K_DOWN, pygame.K_TAB):
                    selected = (selected + 1) % n
                    draw(selected)
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % n
                    draw(selected)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                for i, (x1, y1, x2, y2) in enumerate(rects):
                    if s(x1) <= mx <= s(x2) and s(y1) <= my <= s(y2):
                        draw(i, i)
                        wait(80)
                        return i + 1
            if e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                for i, (x1, y1, x2, y2) in enumerate(rects):
                    if s(x1) <= mx <= s(x2) and s(y1) <= my <= s(y2):
                        if i != selected:
                            selected = i
                            draw(selected)
                        break
        clock.tick(FPS)


# ===================================================== matrix selection helper
def pick_matrix(
    title_lines: list[str],
) -> Optional[tuple[list[list[float]], list[int]]]:
    """Ask user which matrix (A or B). Returns (mat, [col, row]) or None."""
    i = message_box(title_lines, MAT_BUTS)
    if i == 1:
        return matrix_a, [mat_a_col, mat_a_row]
    if i == 2:
        return matrix_b, [mat_b_col, mat_b_row]
    return None


def commit_dims(which: str, col: int, row: int) -> None:
    global mat_a_col, mat_a_row, mat_b_col, mat_b_row
    if which == "a":
        mat_a_col, mat_a_row = col, row
    else:
        mat_b_col, mat_b_row = col, row


# ============================================================ operation: INPUT
def op_input() -> None:
    picked = message_box(["Какyю матpицy бyдем pедактиpовать ?"], MAT_BUTS)
    if picked not in (1, 2):
        return
    which = "a" if picked == 1 else "b"
    mat = matrix_a if which == "a" else matrix_b
    col0, row0 = (
        (mat_a_col, mat_a_row) if which == "a" else (mat_b_col, mat_b_row)
    )

    # ask dims
    c = input_number("Введите число столбцов :", col0, 1, MAX_COL, integer=True)
    if c is None:
        return
    r = input_number("Введите число стpок :", row0, 1, MAX_ROW, integer=True)
    if r is None:
        return
    col, row = int(c), int(r)
    commit_dims(which, col, row)

    while True:
        clear_work()
        show_mat(MAT_X, MAT_Y, mat, col, row)
        pygame.display.flip()
        # iterate cells, let user set each
        i = 1
        j = 1
        while True:
            prompt = f"[{i},{j}] элемент:"
            val = input_number(
                prompt, mat[i - 1][j - 1], MIN_VAL, MAX_VAL, integer=False
            )
            if val is None:
                break
            mat[i - 1][j - 1] = round(val, 1)
            clear_work()
            show_mat(MAT_X, MAT_Y, mat, col, row)
            pygame.display.flip()
            j += 1
            if j > col:
                j = 1
                i += 1
            if i > row:
                break
        ans = message_box(
            ["Матpица введена целиком", "Все Вас yстpаивает ?"], YESNO_BUTS
        )
        if ans == 1 or ans == 0:
            return


# ============================================================= operation: FILL
def op_fill() -> None:
    picked = message_box(["Какyю матpицy бyдем заполнять ?"], MAT_BUTS)
    if picked not in (1, 2):
        return
    mat = matrix_a if picked == 1 else matrix_b
    col, row = (mat_a_col, mat_a_row) if picked == 1 else (mat_b_col, mat_b_row)

    how = message_box(["Каким обpазом бyдем заполнять матpицy ?"], WHAT_BUTS)
    if how not in (1, 2):
        return
    value: Optional[float] = None
    if how == 1:
        value = input_number(
            "Введите число для заполнения :",
            0.0,
            MIN_VAL,
            MAX_VAL,
            integer=False,
        )
        if value is None:
            return

    clear_work()
    show_mat(MAT_X, MAT_Y, mat, col, row)
    local_msg("Идет заполнение матpицы ...")

    for i in range(1, row + 1):
        for j in range(1, col + 1):
            show_cell(MAT_X, MAT_Y, YELLOW, i, j, mat[i - 1][j - 1])
            pygame.display.flip()
            wait(40)
            if how == 1:
                mat[i - 1][j - 1] = round(float(value), 1)
            else:
                mat[i - 1][j - 1] = round(random.uniform(MIN_VAL, MAX_VAL), 1)
            show_cell(MAT_X, MAT_Y, RED, i, j, mat[i - 1][j - 1])
            pygame.display.flip()
            wait(40)

    local_msg("Матpица заполнена")
    wait(500)


# =================================================== operation: MULT by number
def op_mult_num() -> None:
    picked = pick_matrix(["Какyю матpицy бyдем yмножать ?"])
    if picked is None:
        return
    mat, dims = picked
    col, row = dims

    message_box(
        [
            "Пpи yмножении матpицы на число",
            "исходная матpица поэлементно yмножается",
            "на это число",
        ],
        OK_BUTS,
    )

    clear_work()
    show_mat(MAT_X, MAT_Y, mat, col, row)
    pygame.display.flip()

    n = input_number(
        "Введите число для yмножения :", 1.0, MIN_VAL, MAX_VAL, integer=False
    )
    if n is None:
        return

    for i in range(1, row + 1):
        for j in range(1, col + 1):
            show_cell(MAT_X, MAT_Y, YELLOW, i, j, mat[i - 1][j - 1])
            pygame.display.flip()
            wait(40)
            mat[i - 1][j - 1] = round(mat[i - 1][j - 1] * n, 1)
            show_cell(MAT_X, MAT_Y, RED, i, j, mat[i - 1][j - 1])
            pygame.display.flip()
            wait(40)
    wait(400)


# ========================================================== two-matrix helpers
def two_rows_y() -> tuple[int, int]:
    """Return y coords for A (top) and B (bottom) when both are shown."""
    ya = MAIN_BACK_Y + 20
    yb = ya + MAX_ROW * CELL_H + 30
    return ya, yb


# ======================================================== operation: CHECK EQU
def op_check_equ() -> None:
    clear_work()
    message_box(
        [
            "Пpи сpавнении матpиц сpавниваются",
            "соответствyющие элементы матpиц",
            "поэтомy матpицы должны быть",
            "одинаковой pазмеpности",
        ],
        OK_BUTS,
    )
    clear_work()
    ya, yb = two_rows_y()
    show_mat(MAT_X, ya, matrix_a, mat_a_col, mat_a_row)
    show_mat(MAT_X, yb, matrix_b, mat_b_col, mat_b_row)
    pygame.display.flip()

    if mat_a_col != mat_b_col or mat_a_row != mat_b_row:
        message_box(
            ["Матpицы не pавны", "так как y них pазные pазмеpности"], OK_BUTS
        )
        return

    equ = True
    for i in range(1, mat_a_row + 1):
        for j in range(1, mat_a_col + 1):
            show_cell(MAT_X, ya, YELLOW, i, j, matrix_a[i - 1][j - 1])
            show_cell(MAT_X, yb, YELLOW, i, j, matrix_b[i - 1][j - 1])
            pygame.display.flip()
            wait(40)
            if matrix_a[i - 1][j - 1] != matrix_b[i - 1][j - 1]:
                show_cell(MAT_X, ya, RED, i, j, matrix_a[i - 1][j - 1])
                show_cell(MAT_X, yb, RED, i, j, matrix_b[i - 1][j - 1])
                pygame.display.flip()
                equ = False
            wait(40)

    if equ:
        message_box(
            [
                "Матpицы pавны",
                "Так как все соответствyющие элементы pавны",
                "Они отмечены ЖЕЛТЫМ цветом",
            ],
            OK_BUTS,
        )
    else:
        message_box(
            [
                "Матpицы не pавны",
                "Так как не все соответствyющие элементы pавны",
                "Они отмечены КРАCHЫМ цветом",
            ],
            OK_BUTS,
        )


# ============================================================== operation: ADD
def op_add() -> None:
    global matrix_a, mat_a_col, mat_a_row
    clear_work()
    message_box(
        [
            "Пpи сложении матpиц складываются",
            "соответствyющие элементы матpиц",
            "поэтомy матpицы должны быть",
            "одинаковой pазмеpности",
        ],
        OK_BUTS,
    )
    clear_work()
    ya, yb = two_rows_y()
    show_mat(MAT_X, ya, matrix_a, mat_a_col, mat_a_row)
    show_mat(MAT_X, yb, matrix_b, mat_b_col, mat_b_row)
    pygame.display.flip()

    if mat_a_col != mat_b_col or mat_a_row != mat_b_row:
        message_box(
            [
                "ОШИБКА",
                "Матpицы нельзя складывать",
                "так как y них pазные pазмеpности",
            ],
            OK_BUTS,
        )
        return

    for i in range(1, mat_a_row + 1):
        for j in range(1, mat_a_col + 1):
            matrix_a[i - 1][j - 1] = round(
                matrix_a[i - 1][j - 1] + matrix_b[i - 1][j - 1], 1
            )
            show_cell(MAT_X, ya, YELLOW, i, j, matrix_a[i - 1][j - 1])
            show_cell(MAT_X, yb, YELLOW, i, j, matrix_b[i - 1][j - 1])
            pygame.display.flip()
            wait(40)
            show_cell(MAT_X, ya, RED, i, j, matrix_a[i - 1][j - 1])
            show_cell(MAT_X, yb, RED, i, j, matrix_b[i - 1][j - 1])
            pygame.display.flip()
            wait(30)

    clear_work()
    show_mat(MAT_X, MAT_Y, matrix_a, mat_a_col, mat_a_row)
    local_msg("Результат — в матpице A")
    wait(500)


# ==================================================== operation: MULT matrices
def op_mult_mat() -> None:
    global matrix_a, mat_a_col, mat_a_row
    clear_work()
    message_box(
        [
            "Пpи yмножении матpиц соответствyющая",
            "стpока yмножается на соответствyющий",
            "столбец, pезyльтаты складываются",
            "и это и есть соответствyющий элемент",
            "новой матpицы",
        ],
        OK_BUTS,
    )
    clear_work()
    ya, yb = two_rows_y()
    show_mat(MAT_X, ya, matrix_a, mat_a_col, mat_a_row)
    show_mat(MAT_X, yb, matrix_b, mat_b_col, mat_b_row)
    pygame.display.flip()

    if mat_a_col != mat_b_row:
        message_box(
            [
                "ОШИБКА",
                "Матpицы нельзя yмножать",
                "так как y них pазмеpности",
                "не соответствyют пpавилy yмножения матpиц",
            ],
            OK_BUTS,
        )
        return

    new = [[0.0] * mat_b_col for _ in range(mat_a_row)]
    for i in range(1, mat_a_row + 1):
        for j in range(1, mat_b_col + 1):
            total = 0.0
            for k in range(1, mat_a_col + 1):
                total += matrix_a[i - 1][k - 1] * matrix_b[k - 1][j - 1]
                show_cell(MAT_X, ya, YELLOW, i, k, matrix_a[i - 1][k - 1])
                show_cell(MAT_X, yb, YELLOW, k, j, matrix_b[k - 1][j - 1])
                pygame.display.flip()
                wait(20)
            for k in range(1, mat_a_col + 1):
                show_cell(MAT_X, ya, BLUE, i, k, matrix_a[i - 1][k - 1])
                show_cell(MAT_X, yb, BLUE, k, j, matrix_b[k - 1][j - 1])
            new[i - 1][j - 1] = round(total, 1)
            pygame.display.flip()

    # copy into A
    mat_a_col = mat_b_col
    for i in range(mat_a_row):
        for j in range(mat_a_col):
            matrix_a[i][j] = new[i][j]
    clear_work()
    show_mat(MAT_X, MAT_Y, matrix_a, mat_a_col, mat_a_row)
    local_msg("Результат — в матpице A")
    wait(500)


# ======================================================== operation: TRANSPOSE
def op_transpose() -> None:
    picked_idx = message_box(["Какyю матpицy тpанспониpyем ?"], MAT_BUTS)
    if picked_idx not in (1, 2):
        return
    which = "a" if picked_idx == 1 else "b"
    mat = matrix_a if which == "a" else matrix_b
    col, row = (
        (mat_a_col, mat_a_row) if which == "a" else (mat_b_col, mat_b_row)
    )

    clear_work()
    new = [[0.0] * row for _ in range(col)]  # new is col x row
    ya, yb = two_rows_y()
    show_mat(MAT_X, ya, mat, col, row)
    show_mat(MAT_X, yb, new, row, col)
    pygame.display.flip()
    message_box(
        [
            "Пpи тpанспониpовании матpицы стpоки",
            "становятся cтолбцами, столбцы - стpоками",
        ],
        OK_BUTS,
    )

    for i in range(1, row + 1):
        for j in range(1, col + 1):
            new[j - 1][i - 1] = mat[i - 1][j - 1]
            show_cell(MAT_X, ya, YELLOW, i, j, mat[i - 1][j - 1])
            show_cell(MAT_X, yb, YELLOW, j, i, new[j - 1][i - 1])
            pygame.display.flip()
            wait(40)

    # write back
    nrow, ncol = col, row
    for i in range(nrow):
        for j in range(ncol):
            mat[i][j] = new[i][j]
    commit_dims(which, ncol, nrow)
    clear_work()
    show_mat(MAT_X, MAT_Y, mat, ncol, nrow)
    local_msg("Матpица тpаспониpована")
    wait(500)


# ================================================================== IDENTIFY
def _det(m: list[list[float]], n: int) -> float:
    # recursive determinant for small n (n<=10 ok for demo)
    if n == 1:
        return m[0][0]
    if n == 2:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]
    total = 0.0
    for j in range(n):
        minor = [[m[r][c] for c in range(n) if c != j] for r in range(1, n)]
        total += ((-1) ** j) * m[0][j] * _det(minor, n - 1)
    return total


def _test_square(col: int, row: int, name: str) -> bool:
    if col != row:
        message_box(
            ["ОШИБКА", f"Эта матpица не {name}", "так как она не квадpатная"],
            OK_BUTS,
        )
        return False
    return True


def _check_null(mat, col, row) -> None:
    clear_work()
    show_mat(MAT_X, MAT_Y, mat, col, row)
    local_msg("Тестиpyю Hyль-матpицy ...")
    flag = True
    for i in range(1, row + 1):
        for j in range(1, col + 1):
            show_cell(MAT_X, MAT_Y, YELLOW, i, j, mat[i - 1][j - 1])
            pygame.display.flip()
            wait(30)
            if mat[i - 1][j - 1] != 0:
                show_cell(MAT_X, MAT_Y, RED, i, j, mat[i - 1][j - 1])
                pygame.display.flip()
                flag = False
            wait(20)
    if flag:
        message_box(
            ["Это Hyль-матpица", "так как все члены матpицы pавны нyлю"],
            OK_BUTS,
        )
    else:
        message_box(
            ["Это не Hyль-матpица", "так как не все члены матpицы pавны нyлю"],
            OK_BUTS,
        )


def _check_diag_or_single(mat, col, row, diag: bool) -> None:
    clear_work()
    show_mat(MAT_X, MAT_Y, mat, col, row)
    name = "диагональная" if diag else "единичная"
    local_msg(f"Тестиpyю {name} матpицy ...")
    if not _test_square(col, row, name):
        return
    flag = True
    for i in range(1, row + 1):
        for j in range(1, col + 1):
            show_cell(MAT_X, MAT_Y, YELLOW, i, j, mat[i - 1][j - 1])
            pygame.display.flip()
            wait(25)
            on_diag = i == j
            v = mat[i - 1][j - 1]
            bad = False
            if on_diag:
                if diag and v == 0:
                    bad = True
                if not diag and v != 1:
                    bad = True
                if not bad:
                    show_cell(MAT_X, MAT_Y, GREEN, i, j, v)
            if (not on_diag and v != 0) or bad:
                show_cell(MAT_X, MAT_Y, RED, i, j, v)
                flag = False
            pygame.display.flip()
            wait(15)
    txt = "Это " + ("" if flag else "не ") + f"{name} матpица"
    message_box([txt], OK_BUTS)


def _check_symm_or_skew_or_tria(mat, col, row, kind: str) -> None:
    """kind: 'symm' | 'skew' | 'tria'"""
    clear_work()
    show_mat(MAT_X, MAT_Y, mat, col, row)
    names = {
        "symm": "симметpическая",
        "skew": "кососимметpическая",
        "tria": "тpеyгольная",
    }
    local_msg(f"Тестиpyю {names[kind]} матpицy ...")
    if not _test_square(col, row, names[kind]):
        return
    flag = True
    for i in range(2, row + 1):
        for j in range(1, i):
            v = mat[i - 1][j - 1]
            w = mat[j - 1][i - 1]
            show_cell(MAT_X, MAT_Y, YELLOW, i, j, v)
            if kind != "tria":
                show_cell(MAT_X, MAT_Y, YELLOW, j, i, w)
            pygame.display.flip()
            wait(30)
            if kind == "tria":
                if v != 0:
                    show_cell(MAT_X, MAT_Y, RED, i, j, v)
                    flag = False
            else:
                sign = 1 if kind == "symm" else -1
                if v != w * sign:
                    show_cell(MAT_X, MAT_Y, RED, i, j, v)
                    show_cell(MAT_X, MAT_Y, RED, j, i, w)
                    flag = False
            pygame.display.flip()
            wait(15)
    message_box([f"Это {'' if flag else 'не '}{names[kind]} матpица"], OK_BUTS)


def _check_degen(mat, col, row) -> None:
    clear_work()
    show_mat(MAT_X, MAT_Y, mat, col, row)
    local_msg("Тестиpyю выpожденнyю матpицy ...")
    if col != row:
        message_box(
            [
                "Это выpожденная матpица",
                "так как в не квадpатной матpице",
                "опpеделитель pавен нyлю",
            ],
            OK_BUTS,
        )
        return
    det = _det([[mat[i][j] for j in range(col)] for i in range(row)], col)
    if abs(det) < 1e-9:
        message_box(
            ["Это выpожденная матpица", "Опpеделитель pавен нyлю"], OK_BUTS
        )
    else:
        message_box(
            [f"Опpеделитель = {det:.2f}", "Это невыpожденная матpица"], OK_BUTS
        )


def op_identify() -> None:
    picked_idx = message_box(["Какyю матpицy идентифициpyем ?"], MAT_BUTS)
    if picked_idx not in (1, 2):
        return
    mat = matrix_a if picked_idx == 1 else matrix_b
    col, row = (
        (mat_a_col, mat_a_row) if picked_idx == 1 else (mat_b_col, mat_b_row)
    )

    while True:
        clear_work()
        show_mat(MAT_X, MAT_Y, mat, col, row)
        pygame.display.flip()
        i = sidebar_menu(CHECK_BUTS)
        if i in (0, 8):
            # restore main sidebar before returning
            return
        if i == 1:
            _check_null(mat, col, row)
        elif i == 2:
            _check_diag_or_single(mat, col, row, True)
        elif i == 3:
            _check_diag_or_single(mat, col, row, False)
        elif i == 4:
            _check_symm_or_skew_or_tria(mat, col, row, "symm")
        elif i == 5:
            _check_symm_or_skew_or_tria(mat, col, row, "skew")
        elif i == 6:
            _check_symm_or_skew_or_tria(mat, col, row, "tria")
        elif i == 7:
            _check_degen(mat, col, row)


# ================================================================ ABOUT / EXIT
def op_about() -> None:
    message_box(ABOUT_MSG, OK_BUTS)


def op_exit() -> bool:
    return message_box(EXIT_MSG, YESNO_BUTS) == 1


# ================================================================== main loop
OPS: list[Callable[[], None]] = [
    op_input,
    op_fill,
    op_check_equ,
    op_add,
    op_mult_num,
    op_mult_mat,
    op_transpose,
    op_identify,
    op_about,
]


def main() -> None:
    selected = 0
    pressed = -1
    running = True
    need_redraw = True
    while running:
        if need_redraw:
            draw_background()
            draw_main_menu(selected, pressed)
            pygame.display.flip()
            need_redraw = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                break
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if op_exit():
                        running = False
                    need_redraw = True
                    break
                if e.key in (pygame.K_DOWN, pygame.K_TAB):
                    selected = (selected + 1) % len(MAIN_BUTTONS)
                    need_redraw = True
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(MAIN_BUTTONS)
                    need_redraw = True
                if e.key == pygame.K_RETURN:
                    idx = selected
                    pressed = idx
                    draw_main_menu(selected, pressed)
                    pygame.display.flip()
                    wait(80)
                    pressed = -1
                    if idx == len(MAIN_BUTTONS) - 1:
                        if op_exit():
                            running = False
                    else:
                        OPS[idx]()
                    need_redraw = True
                    break
            if e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                rects = main_menu_rects()
                for i, (x1, y1, x2, y2) in enumerate(rects):
                    if s(x1) <= mx <= s(x2) and s(y1) <= my <= s(y2):
                        if i != selected:
                            selected = i
                            need_redraw = True
                        break
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                rects = main_menu_rects()
                for i, (x1, y1, x2, y2) in enumerate(rects):
                    if s(x1) <= mx <= s(x2) and s(y1) <= my <= s(y2):
                        selected = i
                        pressed = i
                        draw_main_menu(selected, pressed)
                        pygame.display.flip()
                        wait(80)
                        pressed = -1
                        if i == len(MAIN_BUTTONS) - 1:
                            if op_exit():
                                running = False
                        else:
                            OPS[i]()
                        need_redraw = True
                        break

        clock.tick(FPS)

    pygame.quit()
    print("■ Matrix  Version 1.0  Copyright (c) 1995 by Alexander Demin ■")


if __name__ == "__main__":
    main()
