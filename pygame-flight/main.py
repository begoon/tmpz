import math
import random
import sys

import pygame

WIDTH, HEIGHT = 1280, 720
FPS = 120

SHIP_WIDTH = 50
SHIP_HEIGHT = 20
SHIP_SPEED = 420.0  # units per second at full stick deflection
SHIP_COLOR = (60, 200, 255)

PROJECTILE_SPEED = 800.0
PROJECTILE_RADIUS = 3
PROJECTILE_COLOR = (255, 240, 120)
FIRE_COOLDOWN = 0.12  # seconds between shots (prevents spam from held button)

# randomized spawn interval (min, max) seconds
OBSTACLE_MIN_INTERVAL = (0.35, 0.85)
OBSTACLE_BASE_SPEED = (200.0, 360.0)  # leftward speed range
OBSTACLE_RADIUS = (12, 30)  # circle size range
OBSTACLE_AMPLITUDE = (30, 140)  # vertical sine amplitude
OBSTACLE_FREQ = (0.8, 2.2)  # cycles per second
OBSTACLE_COLOR = (255, 100, 120)

BG_COLOR = (10, 10, 18)
HUD_COLOR = (180, 200, 220)
DEADZONE = 0.15

LEFT_STICK_X = 0
LEFT_STICK_Y = 1
RB_BUTTON_INDEX = 5
RT_AXIS_INDEX = 5


def clamp(value, lo, hi):
    return lo if value < lo else hi if value > hi else value


def circle_rect_collision(cx, cy, cr, rx, ry, rw, rh):
    # find the closest point on rect to circle center
    closest_x = clamp(cx, rx, rx + rw)
    closest_y = clamp(cy, ry, ry + rh)
    dx = cx - closest_x
    dy = cy - closest_y
    return (dx * dx + dy * dy) <= (cr * cr)


class Ship:
    def __init__(self, x, y):
        self.w = SHIP_WIDTH
        self.h = SHIP_HEIGHT
        self.x = x
        self.y = y
        self.cooldown = 0.0

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x - self.w * 0.5),
            int(self.y - self.h * 0.5),
            self.w,
            self.h,
        )

    @property
    def projectile_firing_position(self):
        return (self.x + self.w * 0.5, self.y)

    def update(self, dt, move_vec):
        self.cooldown = max(0.0, self.cooldown - dt)
        self.x += move_vec[0] * SHIP_SPEED * dt
        self.y += move_vec[1] * SHIP_SPEED * dt
        margin = 10
        self.x = clamp(
            self.x,
            margin + self.w * 0.5,
            WIDTH - margin - self.w * 0.5,
        )
        self.y = clamp(
            self.y,
            margin + self.h * 0.5,
            HEIGHT - margin - self.h * 0.5,
        )

    def can_fire(self):
        return self.cooldown <= 0.0

    def fire(self):
        self.cooldown = FIRE_COOLDOWN
        tipx, tipy = self.projectile_firing_position
        return Projectile(tipx, tipy)

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, SHIP_COLOR, r, 0, border_radius=3)
        nose = [
            (r.right + 10, r.centery),
            (r.right - 3, r.centery - (r.height // 2 - 0)),
            (r.right - 3, r.centery + (r.height // 2 - 2)),
        ]
        pygame.draw.polygon(surf, SHIP_COLOR, nose)


class Projectile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.r = PROJECTILE_RADIUS
        self.alive = True

    def update(self, dt):
        self.x += PROJECTILE_SPEED * dt
        if self.x - self.r > WIDTH + 20:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(
            surf,
            PROJECTILE_COLOR,
            (int(self.x), int(self.y)),
            self.r,
        )


class Obstacle:
    def __init__(self, radius, base_y, amp, freq_hz, phase, speed):
        self.r = radius
        self.base_y = base_y
        self.amp = amp
        self.freq = freq_hz * 2.0 * math.pi  # to radians/sec
        self.phase = phase
        self.speed = speed
        self.t = 0.0
        self.x = WIDTH + self.r + 2
        self.y = base_y
        self.alive = True

    def update(self, dt):
        self.t += dt
        self.x -= self.speed * dt
        self.y = self.base_y + self.amp * math.sin(
            self.freq * self.t + self.phase
        )
        if self.x + self.r < -30:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(
            surf,
            OBSTACLE_COLOR,
            (int(self.x), int(self.y)),
            self.r,
        )


def main():
    pygame.init()
    pygame.display.set_caption("Sine Space Run")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    pygame.joystick.init()
    joysticks = [
        pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
    ]
    for joystick in joysticks:
        joystick.init()

    if joysticks:
        joystick = joysticks[0]
        print("hoystick:", joystick.get_name())
        print(
            "axes:",
            joystick.get_numaxes(),
            "buttons:",
            joystick.get_numbuttons(),
        )
    else:
        joystick = None
        print("no joystick detected, keyboard fallback enabled")

    ship = Ship(120, HEIGHT // 2)

    projectiles = []
    obstacles = []

    def schedule_next_spawn():
        return random.uniform(*OBSTACLE_MIN_INTERVAL)

    spawn_timer = schedule_next_spawn()
    score = 0
    running = True
    game_over = False

    while running:
        ticker = clock.tick(FPS) / 1000.0

        move_x = 0.0
        move_y = 0.0
        shoot_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if joystick:
            x = joystick.get_axis(LEFT_STICK_X)
            y = joystick.get_axis(LEFT_STICK_Y)
            # deadzone
            move_x = 0.0 if abs(x) < DEADZONE else x
            move_y = 0.0 if abs(y) < DEADZONE else y

            # RB button
            if (
                joystick.get_numbuttons() > RB_BUTTON_INDEX
                and joystick.get_button(RB_BUTTON_INDEX)
            ):
                shoot_pressed = True

            # also allow RT axis as shoot if pushed significantly
            if joystick.get_numaxes() > RT_AXIS_INDEX:
                rt_val = joystick.get_axis(RT_AXIS_INDEX)
                # heuristics: on some drivers, rest= -1.0 pressed= +1.0
                # on others [0..1]
                # the second term catches odd mappings
                if rt_val > 0.5 or (rt_val > -0.1 and rt_val < 0.0):
                    # we'll rely on the >0.5 path primarily
                    pass
                if rt_val > 0.5:
                    shoot_pressed = True

        # keyboard fallback
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y += 1.0
        if keys[pygame.K_SPACE]:
            shoot_pressed = True

        # normalize diagonal speed for keyboard fallback
        mag = math.hypot(move_x, move_y)
        if mag > 1e-6:
            move_x /= max(1.0, mag)
            move_y /= max(1.0, mag)

        if not game_over:
            ship.update(ticker, (move_x, move_y))

            if shoot_pressed and ship.can_fire():
                projectiles.append(ship.fire())

            # spawn obstacles
            spawn_timer -= ticker
            if spawn_timer <= 0.0:
                r = random.randint(*OBSTACLE_RADIUS)
                base_y = random.uniform(60, HEIGHT - 60)
                amp = random.uniform(*OBSTACLE_AMPLITUDE)
                freq = random.uniform(*OBSTACLE_FREQ)
                phase = random.uniform(0, math.tau)
                speed = random.uniform(*OBSTACLE_BASE_SPEED)
                obstacles.append(Obstacle(r, base_y, amp, freq, phase, speed))
                spawn_timer = schedule_next_spawn()

            for p in projectiles:
                p.update(ticker)
            for o in obstacles:
                o.update(ticker)

            # collisions: projectile vs obstacle
            for o in obstacles:
                if not o.alive:
                    continue
                for p in projectiles:
                    if not p.alive:
                        continue
                    # projectile is small circle
                    if (p.x - o.x) ** 2 + (p.y - o.y) ** 2 <= (o.r + p.r) ** 2:
                        p.alive = False
                        o.alive = False
                        score += 1

            # collisions: ship vs obstacle (rect vs circle)
            sr = ship.rect
            for o in obstacles:
                if not o.alive:
                    continue
                if circle_rect_collision(o.x, o.y, o.r, sr.x, sr.y, sr.w, sr.h):
                    game_over = True
                    break

            # cleanup
            projectiles = [p for p in projectiles if p.alive]
            obstacles = [o for o in obstacles if o.alive]

        screen.fill(BG_COLOR)

        # stars parallax (simple)
        # (cheap sparkle effect without extra state)
        for i in range(80):
            sx = (i * 137) % WIDTH
            sy = (i * 251) % HEIGHT
            pygame.draw.circle(screen, (30, 30, 45), (sx, sy), 1)

        for p in projectiles:
            p.draw(screen)
        for o in obstacles:
            o.draw(screen)

        ship.draw(screen)

        hud = font.render(f"SCORE: {score}", True, HUD_COLOR)
        screen.blit(hud, (12, 12))

        if game_over:
            over = pygame.font.SysFont(None, 64).render(
                "GAME OVER",
                True,
                (255, 80, 100),
            )
            screen.blit(
                over,
                (
                    WIDTH // 2 - over.get_width() // 2,
                    HEIGHT // 2 - over.get_height() // 2,
                ),
            )
            sub = font.render(
                "Press ESC to quit or R to restart",
                True,
                HUD_COLOR,
            )
            screen.blit(
                sub,
                (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 40),
            )

            keys = pygame.key.get_pressed()

            if keys[pygame.K_ESCAPE]:
                running = False

            if keys[pygame.K_r]:
                ship = Ship(120, HEIGHT // 2)
                projectiles.clear()
                obstacles.clear()
                score = 0
                spawn_timer = schedule_next_spawn()
                game_over = False

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# pixel images::
#  - replace Ship.draw() to blit a ship image centered at (self.x, self.y)
#  - replace Obstacle.draw() to blit an obstacle sprite centered on
#    (self.x, self.y).

if __name__ == "__main__":
    main()
