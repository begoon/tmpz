import curses
import random
import time

# --- Constants ---
WIDTH, HEIGHT = 64, 25
# Border adds 1 cell on each side: total window = WIDTH+2 x HEIGHT+2
BORDER_W, BORDER_H = WIDTH + 2, HEIGHT + 2
PEAK_ROW = 9
FPS = 10
FRAME_DELAY = 1.0 / FPS
LAVA_INTERVAL = 8.0
ASH_SPAWN_INTERVAL = 6
CARRY_TIME = 14.0  # seconds before person falls
CARRY_WARN_TIME = 9.0  # seconds before person turns red

# Station
STATION_LEFT = 55
STATION_RIGHT = 62
STATION_ROOF = 16

# Starting helicopter position (cockpit)
START_X, START_Y = 58, 15

# --- Terrain data (exact positions from example.txt) ---


def build_terrain():
    """Return set of (col, row) for all volcano X positions."""
    terrain = set()

    # Peak cap (normally hidden under lava)
    terrain |= {(37, 9), (38, 9), (39, 9), (40, 9)}
    terrain |= {(35, 10), (36, 10), (41, 10)}

    # Left slope
    left_slope = {
        11: [34],
        12: [33],
        13: [32],
        14: [27, 28, 29, 30, 31],  # platform
        15: [26],
        16: [25],
        17: [23, 24],
        18: [18, 19, 20, 21, 22],  # platform
        19: [16, 17],
        20: [14, 15],
        21: [9, 10, 11, 12, 13],  # platform
        22: [7, 8],
        23: [2, 3, 4, 5, 6],  # platform
        24: [0, 1],
    }

    # Right slope
    right_slope = {
        11: [42],
        12: [43],
        13: [44],
        14: [45, 46],
        15: [47],
        16: [48],
        17: [49, 50],
        18: [51],
        19: [52],
        20: [53, 54],
    }

    for row, cols in left_slope.items():
        for c in cols:
            terrain.add((c, row))
    for row, cols in right_slope.items():
        for c in cols:
            terrain.add((c, row))

    return terrain


# Lava interior bounds per row (left, right) inclusive
LAVA_BOUNDS = {
    9: (37, 40),
    10: (35, 41),
    11: (34, 42),
    12: (33, 43),
    13: (32, 44),
    14: (27, 46),
    15: (26, 47),
    16: (25, 48),
    17: (23, 50),
    18: (18, 51),
    19: (16, 52),
    20: (14, 54),
    21: (9, 54),
    22: (7, 54),
    23: (2, 54),
    24: (0, 54),
}

# Platform definitions: (platform_row, leftmost_col, rightmost_col)
PLATFORMS = [
    (14, 27, 31),
    (18, 18, 22),
    (21, 9, 13),
    (23, 2, 6),
]

# People: (x, y, platform_row)
PEOPLE_DEF = [
    (28, 13, 14),
    (19, 17, 18),
    (10, 20, 21),
    (3, 22, 23),
]


# --- Entity factories ---


def make_helicopter(x, y):
    return {
        "x": x,
        "y": y,
        "direction": -1,
        "carrying": False,
        "alive": True,
        "carry_timer": 0.0,
    }


def make_person(x, y, platform_row):
    return {
        "x": x,
        "y": y,
        "alive": True,
        "rescued": False,
        "wave_timer": 0,
        "platform_row": platform_row,
    }


def make_ash(x, y, vx, vy):
    return {"x": float(x), "y": float(y), "vx": vx, "vy": vy}


def make_soul(x, y):
    return {
        "x": float(x),
        "y": float(y),
        "vx": random.uniform(-0.5, 0.5),
        "vy": random.uniform(-1.0, -0.3),
    }


def make_projectile(x, y, dx):
    return {"x": x, "y": y, "dx": dx}


# --- Helicopter sprite ---


def heli_cells(heli):
    """Return list of (x, y, char) for the helicopter."""
    ox, oy = heli["x"], heli["y"]
    d = heli["direction"]
    cells = []
    # Rotor: -+-
    cells.append((ox - 1, oy - 1, "-"))
    cells.append((ox, oy - 1, "+"))
    cells.append((ox + 1, oy - 1, "-"))
    if d == 1:  # facing right: tail on left, nose on right
        cells.append((ox - 2, oy, "+"))
        cells.append((ox - 1, oy, "-"))
        cells.append((ox, oy, "O"))
    else:  # facing left: tail on right, nose on left
        cells.append((ox, oy, "O"))
        cells.append((ox + 1, oy, "-"))
        cells.append((ox + 2, oy, "+"))
    if heli["carrying"]:
        cells.append((ox, oy + 1, "I"))
    return cells


def heli_nose(heli):
    """Projectile origin (one cell in front of cockpit)."""
    return (heli["x"] + heli["direction"], heli["y"])


def heli_bounding_cells(heli):
    """Return set of (x, y) occupied by helicopter."""
    return {(c[0], c[1]) for c in heli_cells(heli)}


# --- Drawing helpers ---


def safe_addch(win, y, x, ch, attr=0):
    """Draw at game coords (x,y), offset by border."""
    if 0 <= y < HEIGHT and 0 <= x < WIDTH:
        try:
            win.addch(y + 1, x + 1, ch, attr)
        except curses.error:
            pass


def draw_border(win, color):
    """Draw box-drawing border around the game field."""
    try:
        win.addstr(0, 0, "┌" + "─" * WIDTH + "┐", color)
        for r in range(1, HEIGHT + 1):
            win.addstr(r, 0, "│", color)
            win.addstr(r, WIDTH + 1, "│", color)
        win.addstr(HEIGHT + 1, 0, "└" + "─" * WIDTH + "┘", color)
    except curses.error:
        pass


def draw_terrain(win, terrain, color):
    for x, y in terrain:
        safe_addch(win, y, x, "X", color)


def draw_lava(win, lava_level, color):
    for row in range(PEAK_ROW, lava_level + 1):
        bounds = LAVA_BOUNDS.get(row)
        if bounds:
            for c in range(bounds[0], bounds[1] + 1):
                safe_addch(win, row, c, "+", color)


def draw_station(
    win, lives, rescued_count, color_roof, color_wall, color_heli, color_people
):
    # Roof
    for c in range(STATION_LEFT, STATION_RIGHT + 1):
        safe_addch(win, STATION_ROOF, c, "=", color_roof)
    # Walls
    for row in range(STATION_ROOF + 1, HEIGHT):
        safe_addch(win, row, STATION_LEFT, "!", color_wall)
        safe_addch(win, row, STATION_RIGHT, "!", color_wall)
    # Rescued people just below roof
    for i in range(rescued_count):
        safe_addch(
            win,
            STATION_ROOF + 1,
            STATION_LEFT + 1 + i,
            "I",
            color_people,
        )
    # Spare helicopters inside station (facing left: O-+)
    spare_count = max(0, lives - 1)
    spare_positions = [20, 22]  # cockpit Y positions
    for i in range(min(spare_count, len(spare_positions))):
        sy = spare_positions[i]
        sx = 58  # cockpit X
        # Rotor
        safe_addch(win, sy - 1, sx - 1, "-", color_heli)
        safe_addch(win, sy - 1, sx, "+", color_heli)
        safe_addch(win, sy - 1, sx + 1, "-", color_heli)
        # Body facing left: O-+
        safe_addch(win, sy, sx, "O", color_heli)
        safe_addch(win, sy, sx + 1, "-", color_heli)
        safe_addch(win, sy, sx + 2, "+", color_heli)


def draw_heli(win, heli, color, carry_warn_color=None):
    for x, y, ch in heli_cells(heli):
        if ch == "I" and carry_warn_color is not None:
            safe_addch(win, y, x, ch, carry_warn_color)
        else:
            safe_addch(win, y, x, ch, color)


def draw_hud(win, lives, rescued, total, color):
    msg = f" lives:{lives} rescued:{rescued}/{total} "
    x = (WIDTH - len(msg)) // 2 + 1  # center on top border
    try:
        win.addstr(0, x, msg, color)
    except curses.error:
        pass


def run_explosion(win, ox, oy, render_fn):
    """Animate 8 dots radiating from (ox, oy) with acceleration."""
    directions = [
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ]
    # Each dot: [fx, fy, dx, dy, speed]
    dots = [[float(ox), float(oy), dx, dy, 0.3] for dx, dy in directions]

    while dots:
        new_dots = []
        for d in dots:
            d[4] += 0.15  # accelerate
            d[0] += d[2] * d[4]
            d[1] += d[3] * d[4]
            ix, iy = int(d[0]), int(d[1])
            if 0 <= ix < WIDTH and 0 <= iy < HEIGHT:
                new_dots.append(d)
        dots = new_dots
        if not dots:
            break

        render_fn()
        for d in dots:
            safe_addch(win, int(d[1]), int(d[0]), ".", curses.A_BOLD)
        win.refresh()
        time.sleep(FRAME_DELAY)


# --- Collision helpers ---


def cell_in_terrain(x, y, terrain):
    return (x, y) in terrain


def cell_in_station(x, y):
    if y == STATION_ROOF and STATION_LEFT <= x <= STATION_RIGHT:
        return True
    if y > STATION_ROOF and (x == STATION_LEFT or x == STATION_RIGHT):
        return True
    return False


def cell_in_lava(x, y, lava_level):
    if PEAK_ROW <= y <= lava_level:
        bounds = LAVA_BOUNDS.get(y)
        if bounds and bounds[0] <= x <= bounds[1]:
            return True
    return False


def cell_at_station_deposit(x, y):
    return y <= STATION_ROOF and STATION_LEFT <= x <= STATION_RIGHT


def run_person_fall(win, px, py, terrain, lava_level, render_fn):
    """Animate person 'I' falling from (px, py) until hitting ground."""
    y = py
    while y + 1 < HEIGHT:
        ny = y + 1
        if cell_in_terrain(px, ny, terrain) or cell_in_lava(px, ny, lava_level):
            break
        y = ny
        render_fn()
        safe_addch(
            win,
            y,
            px,
            "I",
            curses.color_pair(2) | curses.A_BOLD,
        )
        win.refresh()
        time.sleep(FRAME_DELAY)
    return px, y


# --- Main game ---


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    # Check terminal size
    max_y, max_x = stdscr.getmaxyx()
    if max_y < BORDER_H or max_x < BORDER_W:
        curses.endwin()
        print(
            f"Terminal too small: need {BORDER_W}x{BORDER_H},"
            f" have {max_x}x{max_y}"
        )
        return

    # Colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_BLUE, -1)

    C_TERRAIN = curses.color_pair(1) | curses.A_BOLD
    C_LAVA = curses.color_pair(2) | curses.A_BOLD
    C_HELI = curses.color_pair(3) | curses.A_BOLD
    C_PEOPLE = curses.color_pair(4) | curses.A_BOLD
    C_HUD = curses.color_pair(5) | curses.A_BOLD
    C_ASH = curses.color_pair(5)
    C_SOUL = curses.color_pair(6) | curses.A_BOLD
    C_PROJ = curses.color_pair(7) | curses.A_BOLD
    C_STATION_ROOF = curses.color_pair(4)
    C_STATION_WALL = curses.color_pair(5)

    # Build terrain
    terrain = build_terrain()

    # Initialize entities
    heli = make_helicopter(START_X, START_Y)
    lives = 3
    rescued_count = 0

    people = [make_person(px, py, pr) for px, py, pr in PEOPLE_DEF]
    total_people = len(people)

    ashes = []
    souls = []
    projectiles = []

    lava_level = PEAK_ROW  # peak row starts filled
    lava_timer = 0.0

    frame_count = 0
    wave_toggle = False
    wave_timer = 0.0

    respawn_timer = 0.0
    respawning = False
    game_over = False
    game_over_msg = ""

    last_time = time.time()

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now

        # --- Input ---
        key = -1
        while True:
            k = stdscr.getch()
            if k == -1:
                break
            key = k

        if key == ord("q") or key == ord("Q"):
            break

        if game_over:
            stdscr.erase()
            draw_border(stdscr, C_TERRAIN)
            hint = "Press any key to play or Q to quit."
            try:
                stdscr.addstr(
                    HEIGHT // 2 + 1,
                    max(1, (WIDTH - len(game_over_msg)) // 2 + 1),
                    game_over_msg,
                    C_HUD,
                )
                stdscr.addstr(
                    HEIGHT // 2 + 3,
                    max(1, (WIDTH - len(hint)) // 2 + 1),
                    hint,
                    C_HUD,
                )
            except curses.error:
                pass
            stdscr.refresh()
            if key != -1 and key != ord("q") and key != ord("Q"):
                # Restart game
                heli = make_helicopter(START_X, START_Y)
                lives = 3
                rescued_count = 0
                people = [make_person(px, py, pr) for px, py, pr in PEOPLE_DEF]
                total_people = len(people)
                ashes = []
                souls = []
                projectiles = []
                lava_level = PEAK_ROW
                lava_timer = 0.0
                respawning = False
                game_over = False
                game_over_msg = ""
            time.sleep(FRAME_DELAY)
            continue

        # --- Render helper (closure over current mutable state) ---
        def render_world():
            stdscr.erase()
            draw_border(stdscr, C_TERRAIN)
            draw_terrain(stdscr, terrain, C_TERRAIN)
            draw_lava(stdscr, lava_level, C_LAVA)
            draw_station(
                stdscr,
                lives,
                rescued_count,
                C_STATION_ROOF,
                C_STATION_WALL,
                C_HELI,
                C_PEOPLE,
            )
            for person in people:
                if person["alive"] and not person["rescued"]:
                    ch = "Y" if wave_toggle else "I"
                    safe_addch(
                        stdscr,
                        person["y"],
                        person["x"],
                        ch,
                        C_PEOPLE,
                    )
            for a in ashes:
                safe_addch(
                    stdscr,
                    int(a["y"]),
                    int(a["x"]),
                    "*",
                    C_ASH,
                )
            for s in souls:
                ix, iy = int(s["x"]), int(s["y"])
                safe_addch(stdscr, iy, ix, "(", C_SOUL)
                safe_addch(stdscr, iy, ix + 1, ")", C_SOUL)
            for p in projectiles:
                safe_addch(
                    stdscr,
                    p["y"],
                    p["x"],
                    "-",
                    C_PROJ,
                )
            if heli["alive"] and not respawning:
                warn = None
                if heli["carrying"] and heli["carry_timer"] >= CARRY_WARN_TIME:
                    warn = C_LAVA  # red
                draw_heli(stdscr, heli, C_HELI, warn)
            draw_hud(
                stdscr,
                lives,
                rescued_count,
                total_people,
                C_HUD,
            )

        # --- Update helicopter ---
        if heli["alive"] and not respawning:
            if key == curses.KEY_UP:
                heli["y"] -= 1
            elif key == curses.KEY_DOWN:
                heli["y"] += 1
            elif key == curses.KEY_LEFT:
                if heli["direction"] != -1:
                    heli["direction"] = -1
                    heli["x"] -= 1  # O shifts toward new direction
                else:
                    heli["x"] -= 1
            elif key == curses.KEY_RIGHT:
                if heli["direction"] != 1:
                    heli["direction"] = 1
                    heli["x"] += 1  # O shifts toward new direction
                else:
                    heli["x"] += 1
            elif key == ord(" "):
                nx, ny = heli_nose(heli)
                projectiles.append(make_projectile(nx, ny, heli["direction"]))

            # Clamp to screen
            heli["x"] = max(2, min(WIDTH - 3, heli["x"]))
            heli["y"] = max(1, min(HEIGHT - 2, heli["y"]))

            # Check deposit before collision (person touching roof)
            if heli["carrying"]:
                py = heli["y"] + 1
                if (
                    py == STATION_ROOF
                    and STATION_LEFT <= heli["x"] <= STATION_RIGHT
                ):
                    heli["carrying"] = False
                    rescued_count += 1
                    if rescued_count == total_people:
                        game_over = True
                        game_over_msg = f"YOU WIN! All {total_people} rescued!"
                    else:
                        alive_left = sum(
                            1 for p in people if p["alive"] and not p["rescued"]
                        )
                        if alive_left == 0:
                            game_over = True
                            game_over_msg = (
                                "GAME OVER - Rescued "
                                f"{rescued_count}/{total_people}"
                            )

            # Check terrain/station/lava collision
            heli_set = heli_bounding_cells(heli)
            ox, oy = heli["x"], heli["y"]
            crash = False
            safe_block = False
            for cx, cy in heli_set:
                if cell_in_terrain(cx, cy, terrain) or cell_in_lava(
                    cx, cy, lava_level
                ):
                    crash = True
                    break
                if cell_in_station(cx, cy):
                    # Cockpit O on roof from above = safe block
                    if (
                        cx == ox
                        and cy == oy
                        and cy == STATION_ROOF
                        and STATION_LEFT <= cx <= STATION_RIGHT
                    ):
                        safe_block = True
                    else:
                        crash = True
                        break
            if crash:
                # Undo move first, then explode
                if key == curses.KEY_UP:
                    heli["y"] += 1
                elif key == curses.KEY_DOWN:
                    heli["y"] -= 1
                elif key == curses.KEY_LEFT:
                    heli["x"] += 1
                elif key == curses.KEY_RIGHT:
                    heli["x"] -= 1
                ex, ey = heli["x"], heli["y"]
                was_carrying = heli["carrying"]
                heli["alive"] = False
                heli["carrying"] = False
                lives -= 1
                run_explosion(stdscr, ex, ey, render_world)
                if was_carrying:
                    souls.append(make_soul(ex, ey))
                if lives <= 0:
                    game_over = True
                    game_over_msg = (
                        "GAME OVER - Rescued " f"{rescued_count}/{total_people}"
                    )
                else:
                    respawning = True
                    respawn_timer = 1.0
            elif safe_block:
                # Just undo the move
                if key == curses.KEY_UP:
                    heli["y"] += 1
                elif key == curses.KEY_DOWN:
                    heli["y"] -= 1
                elif key == curses.KEY_LEFT:
                    heli["x"] += 1
                elif key == curses.KEY_RIGHT:
                    heli["x"] -= 1

        # --- Respawn ---
        if respawning:
            respawn_timer -= dt
            if respawn_timer <= 0:
                respawning = False
                heli = make_helicopter(START_X, START_Y)

        # --- Ash spawning ---
        if frame_count % ASH_SPAWN_INTERVAL == 0:
            ax = random.uniform(37, 40)  # peak cols
            ay = float(PEAK_ROW)
            avx = random.uniform(-0.8, 0.8)
            avy = random.uniform(-0.7, -0.25)
            ashes.append(make_ash(ax, ay, avx, avy))

        # --- Update ashes ---
        new_ashes = []
        for a in ashes:
            a["vy"] -= 0.01
            a["vx"] += random.uniform(-0.08, 0.08)
            a["x"] += a["vx"] * 0.5
            a["y"] += a["vy"] * 0.5
            ix, iy = int(a["x"]), int(a["y"])
            # Remove if off-screen or hitting terrain/station
            if not (0 <= ix < WIDTH and 0 <= iy < HEIGHT):
                continue
            if cell_in_terrain(ix, iy, terrain) or cell_in_station(ix, iy):
                continue
            new_ashes.append(a)
        ashes = new_ashes

        # --- Update projectiles ---
        new_proj = []
        for p in projectiles:
            p["x"] += p["dx"] * 2
            if not (0 <= p["x"] < WIDTH):
                continue
            if cell_in_terrain(p["x"], p["y"], terrain) or cell_in_station(
                p["x"], p["y"]
            ):
                continue
            new_proj.append(p)
        projectiles = new_proj

        # --- Projectile vs ash ---
        surviving_ashes = []
        for a in ashes:
            ix, iy = int(a["x"]), int(a["y"])
            hit = False
            remaining_proj = []
            for p in projectiles:
                if p["x"] == ix and p["y"] == iy:
                    hit = True
                else:
                    remaining_proj.append(p)
            projectiles = remaining_proj
            if not hit:
                surviving_ashes.append(a)
        ashes = surviving_ashes

        # --- Ash/soul vs helicopter ---
        if heli["alive"] and not respawning:
            heli_set = heli_bounding_cells(heli)
            destroyed = False
            for a in ashes:
                if (int(a["x"]), int(a["y"])) in heli_set:
                    destroyed = True
                    break
            if not destroyed:
                for s in souls:
                    sx, sy = int(s["x"]), int(s["y"])
                    if (sx, sy) in heli_set or (sx + 1, sy) in heli_set:
                        destroyed = True
                        break
            if destroyed:
                ex, ey = heli["x"], heli["y"]
                was_carrying = heli["carrying"]
                heli["alive"] = False
                heli["carrying"] = False
                lives -= 1
                run_explosion(stdscr, ex, ey, render_world)
                if was_carrying:
                    souls.append(make_soul(ex, ey))
                if lives <= 0:
                    game_over = True
                    game_over_msg = (
                        "GAME OVER - Rescued " f"{rescued_count}/{total_people}"
                    )
                else:
                    respawning = True
                    respawn_timer = 1.0

        # --- Pick up person ---
        if heli["alive"] and not respawning and not heli["carrying"]:
            ox, oy = heli["x"], heli["y"]  # cockpit O position
            for person in people:
                if person["alive"] and not person["rescued"]:
                    if person["x"] == ox and person["y"] == oy + 1:
                        person["alive"] = False
                        person["rescued"] = True
                        heli["carrying"] = True
                        heli["carry_timer"] = 0.0
                        break

        # --- Carry timer / person fall ---
        if heli["alive"] and not respawning and heli["carrying"]:
            heli["carry_timer"] += dt
            if heli["carry_timer"] >= CARRY_TIME:
                # Person falls
                heli["carrying"] = False
                fx, fy = run_person_fall(
                    stdscr,
                    heli["x"],
                    heli["y"] + 1,
                    terrain,
                    lava_level,
                    render_world,
                )
                souls.append(make_soul(fx, fy))
                # Check end condition
                alive_left = sum(
                    1 for p in people if p["alive"] and not p["rescued"]
                )
                if alive_left == 0 and not game_over:
                    game_over = True
                    game_over_msg = (
                        "GAME OVER - Rescued " f"{rescued_count}/{total_people}"
                    )

        # --- Lava ---
        lava_timer += dt
        if lava_timer >= LAVA_INTERVAL:
            lava_timer -= LAVA_INTERVAL
            if lava_level < HEIGHT - 1:
                lava_level += 1

                # Kill people whose platform is now under lava
                for person in people:
                    if person["alive"] and not person["rescued"]:
                        if lava_level >= person["platform_row"]:
                            person["alive"] = False
                            souls.append(make_soul(person["x"], person["y"]))

                # Check end condition
                alive_left = sum(
                    1 for p in people if p["alive"] and not p["rescued"]
                )
                carrying = 1 if (heli["alive"] and heli["carrying"]) else 0
                if alive_left == 0 and carrying == 0 and not game_over:
                    game_over = True
                    game_over_msg = (
                        f"GAME OVER - Rescued {rescued_count}/{total_people}"
                    )

        # --- Update souls ---
        for s in souls:
            s["vy"] += random.uniform(-0.1, 0.03)
            s["vx"] += random.uniform(-0.1, 0.1)
            nx = s["x"] + s["vx"] * 0.4
            ny = s["y"] + s["vy"] * 0.4
            ix, iy = int(nx), int(ny)
            # Bounce off screen edges
            if nx < 0:
                nx, s["vx"] = 0, abs(s["vx"])
            if nx >= WIDTH - 1:
                nx, s["vx"] = WIDTH - 2, -abs(s["vx"])
            if ny < 0:
                ny, s["vy"] = 0, abs(s["vy"])
            if ny >= HEIGHT:
                ny, s["vy"] = HEIGHT - 1, -abs(s["vy"])
            # Bounce off volcano terrain, station, and lava
            # Check BOTH characters: '(' at (ix, iy) and ')' at (ix+1, iy)
            ix, iy = int(nx), int(ny)
            blocked = False
            for cx in (ix, ix + 1):
                if (
                    cell_in_terrain(cx, iy, terrain)
                    or cell_in_station(cx, iy)
                    or cell_in_lava(cx, iy, lava_level)
                ):
                    blocked = True
                    break
            if blocked:
                s["vx"] = -s["vx"]
                s["vy"] = -s["vy"]
            else:
                s["x"] = nx
                s["y"] = ny

        # --- Wave animation ---
        wave_timer += dt
        if wave_timer >= 0.5:
            wave_timer -= 0.5
            wave_toggle = not wave_toggle

        # --- Render ---
        render_world()

        stdscr.refresh()

        frame_count += 1
        elapsed = time.time() - now
        sleep_time = FRAME_DELAY - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


if __name__ == "__main__":
    curses.wrapper(main)
