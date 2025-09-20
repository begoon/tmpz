import math
import sys

import pygame

WIDTH, HEIGHT = 1024, 768
BG_COLOR = (12, 18, 28)
TANK_COLOR = (230, 240, 255)
GUN_COLOR = (180, 220, 255)
BULLET_COLOR = (255, 230, 120)

TANK_SIZE = 32  # square 32x32
TANK_MAX_SPEED = 260.0  # px/s
TANK_ACCEL = 520.0  # px/s^2 when trigger fully pressed

BULLET_SPEED = 560.0  # px/s
BULLET_RADIUS = 4
BULLET_COOLDOWN = 0.12  # seconds between shots

DEADZONE = 0.15

AXIS_LX = 0
AXIS_LY = 1

# right stick (aiming)
AXIS_RX = 2
AXIS_RY = 3

AXIS_LT = 4  # left trigger (accelerate)
AXIS_RT = 5  # right trigger (slowdown)

BTN_FIRE = 10  # right pad button (fire)

GUN_SPRITE_ORIENTATION = "vertical_down"  # matches your PNG
GUN_TIP_MARGIN_PX = 0

TURRET_VERTICAL_OFFSET_FACTOR = 0.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def length(vx, vy):
    return math.hypot(vx, vy)


def deadzone(x, deadzone=DEADZONE):
    return 0.0 if abs(x) < deadzone else x


def adjust_turret_image(src, orientation=GUN_SPRITE_ORIENTATION):
    w, h = src.get_width(), src.get_height()

    if orientation == "vertical_up":
        rotation_offset = 90
        barrel_length_px = h
    elif orientation == "vertical_down":
        rotation_offset = 90
        barrel_length_px = h
    elif orientation == "horizontal_right":
        rotation_offset = 0
        barrel_length_px = w
    elif orientation == "horizontal_left":
        rotation_offset = 180
        barrel_length_px = w
    else:
        rotation_offset = 0
        barrel_length_px = w

    pad = max(w, h)
    pivot_w, pivot_h = w + 2 * pad, h + 2 * pad
    pivot_image = pygame.Surface((pivot_w, pivot_h), pygame.SRCALPHA)

    shift_x = pad + (w / 2 - w / 2)
    shift_y = pad + (h / 2 - h / 2)
    pivot_image.blit(src, (int(shift_x), int(shift_y)))

    return pivot_image, rotation_offset, int(barrel_length_px)


class Bullet:
    __slots__ = ("x", "y", "vx", "vy")

    def __init__(self, x, y, angle):
        cos_a, sin_a = -math.cos(angle), -math.sin(angle)
        self.vx = cos_a * BULLET_SPEED
        self.vy = sin_a * BULLET_SPEED
        self.x = x
        self.y = y

    def update(self, ticker):
        self.x += self.vx * ticker
        self.y += self.vy * ticker
        return 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT

    def draw(self, surf):
        pygame.draw.circle(
            surf,
            BULLET_COLOR,
            (int(self.x), int(self.y)),
            BULLET_RADIUS,
        )


class Tank:
    def __init__(self, x, y, base_image=None, turret_image=None):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.body_angle = 0.0
        self.turret_angle = 0.0
        self.time_since_shot = 0.0

        self.tank_image = base_image
        if self.tank_image is None:
            self.tank_image = pygame.Surface(
                (TANK_SIZE, TANK_SIZE),
                pygame.SRCALPHA,
            )
            self.tank_image.fill((60, 180, 60))
            pygame.draw.rect(
                self.tank_image,
                (40, 120, 40),
                self.tank_image.get_rect(),
                4,
            )

        if turret_image is None:
            turret_image = pygame.Surface(
                (max(10, TANK_SIZE // 6), TANK_SIZE),
                pygame.SRCALPHA,
            )
            turret_image.fill(
                (100, 100, 100),
                pygame.Rect(
                    0,
                    0,
                    turret_image.get_width(),
                    turret_image.get_height() - 10,
                ),
            )

        (
            self.turret_pivot_image,
            self.turret_rotation_offset,
            self.turret_length_px,
        ) = adjust_turret_image(turret_image)

    def update(self, ticker, joystick):
        left_x = deadzone(joystick.get_axis(AXIS_LX)) if joystick else 0.0
        left_y = deadzone(joystick.get_axis(AXIS_LY)) if joystick else 0.0

        right_x = deadzone(joystick.get_axis(AXIS_RX)) if joystick else 0.0
        right_y = deadzone(joystick.get_axis(AXIS_RY)) if joystick else 0.0

        if abs(left_x) > 0.0 or abs(left_y) > 0.0:
            self.body_angle = math.atan2(-left_y, left_x)

        left_pedal = joystick.get_axis(AXIS_LT) if joystick else -1.0
        right_pedal = joystick.get_axis(AXIS_RT) if joystick else -1.0
        acceleration = clamp((left_pedal + 1.0) * 0.5, 0.0, 1.0)
        slowdown = clamp((right_pedal + 1.0) * 0.5, 0.0, 1.0)

        speed = length(self.vx, self.vy)
        speed += (acceleration * TANK_ACCEL - slowdown * TANK_ACCEL) * ticker
        speed = clamp(speed, 0.0, TANK_MAX_SPEED)

        self.vx = math.cos(self.body_angle) * speed
        self.vy = -math.sin(self.body_angle) * speed

        self.x += self.vx * ticker
        self.y += self.vy * ticker

        bounce = -0.25
        if self.x < TANK_SIZE / 2:
            self.x = TANK_SIZE / 2
            self.vx *= bounce
        elif self.x > WIDTH - TANK_SIZE / 2:
            self.x = WIDTH - TANK_SIZE / 2
            self.vx *= bounce
        if self.y < TANK_SIZE / 2:
            self.y = TANK_SIZE / 2
            self.vy *= bounce
        elif self.y > HEIGHT - TANK_SIZE / 2:
            self.y = HEIGHT - TANK_SIZE / 2
            self.vy *= bounce

        if abs(right_x) > 0.0 or abs(right_y) > 0.0:
            self.turret_angle = math.atan2(-right_y, -right_x)

        self.time_since_shot += ticker

    def try_fire(self):
        if self.time_since_shot >= BULLET_COOLDOWN:
            self.time_since_shot = 0.0
            tip_offset = self.turret_length_px + GUN_TIP_MARGIN_PX
            mx = self.x + math.cos(self.turret_angle) * (tip_offset * -1)
            my = self.y - math.sin(self.turret_angle) * (tip_offset * 1)
            return Bullet(mx, my, self.turret_angle)
        return None

    def draw(self, surface):
        rotated_tank = pygame.transform.rotate(
            self.tank_image,
            math.degrees(self.body_angle - math.pi / 2),
        )
        rotated_tank_rect = rotated_tank.get_rect(center=(self.x, self.y))
        surface.blit(rotated_tank, rotated_tank_rect)

        angle = -math.degrees(self.turret_angle) + self.turret_rotation_offset
        rotated_turret = pygame.transform.rotate(self.turret_pivot_image, angle)

        ox = TURRET_VERTICAL_OFFSET_FACTOR * TANK_SIZE
        turret_rect = rotated_turret.get_rect(center=(self.x + ox, self.y))
        surface.blit(rotated_turret, turret_rect)


def main():
    pygame.init()
    pygame.display.set_caption("Tank (xbox controller)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    joystick = None
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(
            f"joystick: {joystick.get_name()}, "
            f"{joystick.get_numaxes()} axes, "
            f"{joystick.get_numbuttons()} buttons"
        )
    else:
        print("joystick not found")
        exit(1)

    tank_image = turret_image = None
    try:
        tank_image = pygame.image.load("assets/tank_base.png").convert_alpha()
        tank_image = pygame.transform.smoothscale(
            tank_image,
            (TANK_SIZE, TANK_SIZE),
        )
        turret_image = pygame.image.load(
            "assets/tank_turret.png"
        ).convert_alpha()
    except Exception:
        print("sprites not found, using vector fallback")

    tank = Tank(WIDTH // 2, HEIGHT // 2, tank_image, turret_image)
    bullets = []

    running = True
    while running:
        ticker = clock.tick(120) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == BTN_FIRE:
                    bullet = tank.try_fire()
                    if bullet:
                        bullets.append(bullet)

        if joystick and joystick.get_button(BTN_FIRE):
            bullet = tank.try_fire()
            if bullet:
                bullets.append(bullet)

        tank.update(ticker, joystick)
        bullets = [bullet for bullet in bullets if bullet.update(ticker)]

        screen.fill(BG_COLOR)
        tank.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)

        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
