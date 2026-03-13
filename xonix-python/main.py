import curses
import time
import random

EMPTY = 0
BORDER = 1
FILLED = 2
TRAIL = 3

WIDTH = 60
HEIGHT = 25


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])


class Game:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.grid = [[EMPTY] * self.width for _ in range(self.height)]
        self.player_x = self.width // 2
        self.player_y = 0
        self.lives = 3
        self.level = 1
        self.balls = []
        self.trail = []
        self.on_border = True
        self.moving_dx = 0
        self.moving_dy = 0
        self.game_over = False
        self.won = False
        self.fill_percent = 0
        self.target_percent = 75
        self.last_ball_time = time.time()
        self.ball_interval = 20

        self._init_borders()
        self._spawn_balls(2)

    def _init_borders(self):
        for x in range(self.width):
            self.grid[0][x] = BORDER
            self.grid[self.height - 1][x] = BORDER
        for y in range(self.height):
            self.grid[y][0] = BORDER
            self.grid[y][self.width - 1] = BORDER

    def _spawn_balls(self, count):
        for _ in range(count):
            for _attempt in range(1000):
                x = random.randint(5, self.width - 6)
                y = random.randint(5, self.height - 6)
                if self.grid[y][x] == EMPTY:
                    self.balls.append(Ball(x, y))
                    break

    def _is_solid(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return self.grid[y][x] in (BORDER, FILLED)

    def move_balls(self):
        for ball in self.balls:
            nx = ball.x + ball.dx
            ny = ball.y + ball.dy

            solid_nx_ny = self._is_solid(nx, ny)
            solid_nx_y = self._is_solid(nx, ball.y)
            solid_x_ny = self._is_solid(ball.x, ny)

            if solid_nx_ny:
                if solid_nx_y and solid_x_ny:
                    ball.dx = -ball.dx
                    ball.dy = -ball.dy
                elif solid_nx_y:
                    ball.dx = -ball.dx
                elif solid_x_ny:
                    ball.dy = -ball.dy
                else:
                    ball.dx = -ball.dx
                    ball.dy = -ball.dy

                nx = ball.x + ball.dx
                ny = ball.y + ball.dy
                if self._is_solid(nx, ny):
                    continue

            ball.x = nx
            ball.y = ny

            if self.grid[ball.y][ball.x] == TRAIL:
                self._lose_life()
                return

    def _lose_life(self):
        self.lives -= 1
        for tx, ty in self.trail:
            self.grid[ty][tx] = EMPTY
        self.trail = []
        self.player_x = self.width // 2
        self.player_y = 0
        self.on_border = True
        self.moving_dx = 0
        self.moving_dy = 0
        if self.lives <= 0:
            self.game_over = True

    def _fill_area(self):
        for tx, ty in self.trail:
            self.grid[ty][tx] = FILLED
        self.trail = []

        reachable = set()
        for ball in self.balls:
            if self.grid[ball.y][ball.x] != EMPTY:
                continue
            stack = [(ball.x, ball.y)]
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in reachable:
                    continue
                if cx < 0 or cx >= self.width or cy < 0 or cy >= self.height:
                    continue
                if self.grid[cy][cx] != EMPTY:
                    continue
                reachable.add((cx, cy))
                stack.append((cx + 1, cy))
                stack.append((cx - 1, cy))
                stack.append((cx, cy + 1))
                stack.append((cx, cy - 1))

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == EMPTY and (x, y) not in reachable:
                    self.grid[y][x] = FILLED

        self._update_fill_percent()

    def _update_fill_percent(self):
        total = (self.width - 2) * (self.height - 2)
        filled = sum(
            1
            for y in range(1, self.height - 1)
            for x in range(1, self.width - 1)
            if self.grid[y][x] == FILLED
        )
        self.fill_percent = int(filled * 100 / total)

    def move_player(self, dx, dy):
        nx = self.player_x + dx
        ny = self.player_y + dy

        if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height:
            return

        cell = self.grid[ny][nx]

        if self.on_border:
            if cell in (BORDER, FILLED):
                self.player_x = nx
                self.player_y = ny
            elif cell == EMPTY:
                self.on_border = False
                self.trail.append((nx, ny))
                self.grid[ny][nx] = TRAIL
                self.player_x = nx
                self.player_y = ny
                self.moving_dx = dx
                self.moving_dy = dy
        else:
            if cell == TRAIL:
                self._lose_life()
            elif cell in (BORDER, FILLED):
                self.player_x = nx
                self.player_y = ny
                self.on_border = True
                self.moving_dx = 0
                self.moving_dy = 0
                self._fill_area()
            elif cell == EMPTY:
                self.trail.append((nx, ny))
                self.grid[ny][nx] = TRAIL
                self.player_x = nx
                self.player_y = ny

    def check_level(self):
        if self.fill_percent >= self.target_percent:
            self.level += 1
            num_balls = len(self.balls) + 1
            self.grid = [[EMPTY] * self.width for _ in range(self.height)]
            self._init_borders()
            self.balls = []
            self._spawn_balls(num_balls)
            self.player_x = self.width // 2
            self.player_y = 0
            self.on_border = True
            self.trail = []
            self.moving_dx = 0
            self.moving_dy = 0
            self.fill_percent = 0
            self.last_ball_time = time.time()

    def maybe_add_ball(self):
        now = time.time()
        if now - self.last_ball_time >= self.ball_interval:
            self._spawn_balls(1)
            self.last_ball_time = now


def draw(stdscr, game):
    stdscr.erase()
    rows, cols = stdscr.getmaxyx()

    status = (
        f" Lives: {game.lives} | "
        f"Filled: {game.fill_percent}%/{game.target_percent}% | "
        f"Level: {game.level} | "
        f"Balls: {len(game.balls)} "
    )
    try:
        stdscr.addnstr(0, 0, status, cols - 1, curses.A_REVERSE)
    except curses.error:
        pass

    ball_positions = {(b.x, b.y) for b in game.balls}

    for y in range(game.height):
        screen_y = y + 1
        if screen_y >= rows:
            break
        for x in range(game.width):
            if x >= cols - 1:
                break

            if x == game.player_x and y == game.player_y:
                ch, attr = "X", curses.color_pair(4) | curses.A_BOLD
            elif (x, y) in ball_positions:
                ch, attr = "O", curses.color_pair(5) | curses.A_BOLD
            elif game.grid[y][x] == BORDER:
                ch, attr = "*", curses.color_pair(1) | curses.A_BOLD
            elif game.grid[y][x] == FILLED:
                ch, attr = ".", curses.color_pair(2)
            elif game.grid[y][x] == TRAIL:
                ch, attr = "+", curses.color_pair(3) | curses.A_BOLD
            else:
                continue

            try:
                stdscr.addstr(screen_y, x, ch, attr)
            except curses.error:
                pass

    hint_y = game.height + 2
    if hint_y < rows:
        try:
            stdscr.addnstr(hint_y, 0, " Arrows: move | q: quit ", cols - 1)
        except curses.error:
            pass

    stdscr.refresh()


def draw_game_over(stdscr, game):
    stdscr.erase()
    rows, cols = stdscr.getmaxyx()
    cy = rows // 2

    lines = [
        f"GAME OVER!  Level: {game.level}  Filled: {game.fill_percent}%",
        "",
        "Press 'r' to restart, 'q' to quit",
    ]
    for i, line in enumerate(lines):
        y = cy - 1 + i
        x = max(0, cols // 2 - len(line) // 2)
        if 0 <= y < rows:
            try:
                stdscr.addnstr(y, x, line, cols - 1)
            except curses.error:
                pass

    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(40)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)

    game = Game()
    last_ball_move = time.time()
    ball_speed = 0.10
    last_auto_move = time.time()
    auto_speed = 0.07

    while True:
        key = stdscr.getch()

        if key == ord("q") or key == 27:
            break

        if game.game_over:
            draw_game_over(stdscr, game)
            if key == ord("r"):
                game = Game()
                last_ball_move = time.time()
                last_auto_move = time.time()
            continue

        if key == curses.KEY_UP:
            game.move_player(0, -1)
            if not game.on_border:
                game.moving_dx, game.moving_dy = 0, -1
            last_auto_move = time.time()
        elif key == curses.KEY_DOWN:
            game.move_player(0, 1)
            if not game.on_border:
                game.moving_dx, game.moving_dy = 0, 1
            last_auto_move = time.time()
        elif key == curses.KEY_LEFT:
            game.move_player(-1, 0)
            if not game.on_border:
                game.moving_dx, game.moving_dy = -1, 0
            last_auto_move = time.time()
        elif key == curses.KEY_RIGHT:
            game.move_player(1, 0)
            if not game.on_border:
                game.moving_dx, game.moving_dy = 1, 0
            last_auto_move = time.time()

        now = time.time()

        if not game.on_border and now - last_auto_move >= auto_speed:
            if game.moving_dx != 0 or game.moving_dy != 0:
                game.move_player(game.moving_dx, game.moving_dy)
            last_auto_move = now

        if now - last_ball_move >= ball_speed:
            game.move_balls()
            last_ball_move = now

        game.maybe_add_ball()
        game.check_level()

        draw(stdscr, game)


if __name__ == "__main__":
    curses.wrapper(main)
