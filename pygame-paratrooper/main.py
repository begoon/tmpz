import math
import random
import sys
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT = 960, 600
FPS = 60
GROUND_Y = HEIGHT - 40

# turret rotation: almost 180° sweep, but not fully horizontal
MIN_ANGLE_DEG = 10  # 0° is facing right/east, 90° is straight up.
MAX_ANGLE_DEG = 175
BARREL_LEN = 60
TURRET_BASE_WIDTH = 120
TURRET_BASE_HEIGHT = 26
TURRET_PIVOT = pygame.Vector2(WIDTH // 2, GROUND_Y)

AXIS_INDEX = 0  # Left stick X axis (most common)
# Right Bumper (the button above the right trigger).
SHOOT_BUTTON_INDEX = 5
AXIS_DEADZONE = 0.15
TURRET_ROT_SPEED_DEG = 150  # degrees per second at full tilt

PROJECTILE_SPEED = 520.0
PROJECTILE_RADIUS = 4
FIRE_COOLDOWN = 0.12  # seconds

HELI_SPEED_RANGE = (80, 140)
HELI_SPAWN_EVERY = (1.2, 2.4)  # seconds (min, max)
HELI_SIZE = (70, 22)
HELI_LEVELS = None  # set in Game.__init__ based on HEIGHT
HELI_DROP_CHANCE_PER_SEC = 0.55  # probability per second to drop a trooper

TROOPER_SIZE = 12
FREEFALL_SPEED = 280
PARACHUTE_SPEED = 70
PARACHUTE_OPEN_DELAY_RANGE = (0.35, 1.0)  # seconds after drop

MAX_LANDED = 5


@dataclass
class Projectile:
    pos: pygame.Vector2
    vel: pygame.Vector2
    alive: bool = True

    def update(self, dt: float):
        if not self.alive:
            return
        self.pos += self.vel * dt
        # Despawn when off-screen
        if (
            self.pos.x < -20
            or self.pos.x > WIDTH + 20
            or self.pos.y < -20
            or self.pos.y > HEIGHT + 20
        ):
            self.alive = False

    def draw(self, surf: pygame.Surface):
        if self.alive:
            pygame.draw.circle(
                surf,
                (240, 240, 240),
                (int(self.pos.x), int(self.pos.y)),
                PROJECTILE_RADIUS,
            )

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.pos.x - PROJECTILE_RADIUS),
            int(self.pos.y - PROJECTILE_RADIUS),
            PROJECTILE_RADIUS * 2,
            PROJECTILE_RADIUS * 2,
        )


@dataclass
class Paratrooper:
    pos: pygame.Vector2
    open_after: float
    time_since_drop: float = 0.0
    parachute_open: bool = False
    alive: bool = True
    landed: bool = False

    def update(self, dt: float):
        if not self.alive:
            return
        self.time_since_drop += dt
        if not self.parachute_open and self.time_since_drop >= self.open_after:
            self.parachute_open = True
        vy = PARACHUTE_SPEED if self.parachute_open else FREEFALL_SPEED
        self.pos.y += vy * dt
        if self.pos.y + TROOPER_SIZE >= GROUND_Y:
            self.pos.y = GROUND_Y - TROOPER_SIZE
            self.alive = False
            self.landed = True

    def draw(self, surf: pygame.Surface):
        rect = pygame.Rect(
            int(self.pos.x),
            int(self.pos.y),
            TROOPER_SIZE,
            TROOPER_SIZE,
        )
        pygame.draw.rect(surf, (220, 220, 0), rect)
        if self.parachute_open:
            arc_w, arc_h = TROOPER_SIZE * 2, TROOPER_SIZE
            arc_rect = pygame.Rect(
                int(self.pos.x - (arc_w - TROOPER_SIZE) // 2),
                int(self.pos.y - arc_h - 6),
                arc_w,
                arc_h,
            )
            start_angle = math.pi  # 180°
            end_angle = 2 * math.pi  # 360°
            pygame.draw.arc(
                surf,
                (180, 180, 255),
                arc_rect,
                start_angle,
                end_angle,
                2,
            )
            left_attach = (arc_rect.left + 6, arc_rect.bottom)
            right_attach = (arc_rect.right - 6, arc_rect.bottom)
            trooper_top_left = (rect.left, rect.top)
            trooper_top_right = (rect.right, rect.top)
            pygame.draw.line(
                surf,
                (180, 180, 255),
                left_attach,
                trooper_top_left,
                2,
            )
            pygame.draw.line(
                surf,
                (180, 180, 255),
                right_attach,
                trooper_top_right,
                2,
            )

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.pos.x),
            int(self.pos.y),
            TROOPER_SIZE,
            TROOPER_SIZE,
        )


@dataclass
class Helicopter:
    pos: pygame.Vector2
    speed: float
    direction: int  # +1 right, -1 left
    level_y: int
    last_drop_try: float = 0.0
    alive: bool = True

    def update(self, dt: float):
        if not self.alive:
            return
        self.pos.x += self.speed * self.direction * dt
        # despawn if off-screen beyond margin
        if (self.direction > 0 and self.pos.x > WIDTH + 100) or (
            self.direction < 0 and self.pos.x < -100
        ):
            self.alive = False

    def maybe_drop(self, dt: float) -> list:
        # convert per-second chance into per-frame Bernoulli
        if not self.alive:
            return []
        drop_prob = 1 - math.exp(-HELI_DROP_CHANCE_PER_SEC * dt)
        spawned = []
        if random.random() < drop_prob:
            drop_x = self.pos.x + HELI_SIZE[0] // 2 - TROOPER_SIZE // 2
            trooper = Paratrooper(
                pos=pygame.Vector2(drop_x, self.level_y + HELI_SIZE[1]),
                open_after=random.uniform(*PARACHUTE_OPEN_DELAY_RANGE),
            )
            spawned.append(trooper)
        return spawned

    def draw(self, surf: pygame.Surface):
        body = pygame.Rect(int(self.pos.x), int(self.level_y), *HELI_SIZE)
        pygame.draw.rect(surf, (120, 200, 120), body)
        rotor_y = self.level_y - 6
        pygame.draw.line(
            surf,
            (120, 200, 120),
            (body.left + 6, rotor_y),
            (body.right - 6, rotor_y),
            3,
        )

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.pos.x),
            int(self.level_y),
            HELI_SIZE[0],
            HELI_SIZE[1],
        )


class Turret:
    def __init__(self, pivot: pygame.Vector2):
        self.pivot = pygame.Vector2(pivot)
        self.angle_deg = 90.0  # start straight up
        self.cooldown = 0.0

    def update(self, dt: float, input_amount: float):
        if abs(input_amount) < AXIS_DEADZONE:
            input_amount = 0.0
        self.angle_deg -= input_amount * TURRET_ROT_SPEED_DEG * dt
        self.angle_deg = max(MIN_ANGLE_DEG, min(MAX_ANGLE_DEG, self.angle_deg))
        if self.cooldown > 0:
            self.cooldown -= dt

    def barrel_tip(self) -> pygame.Vector2:
        rad = math.radians(self.angle_deg)
        dir_vec = pygame.Vector2(math.cos(rad), -math.sin(rad))
        return self.pivot + dir_vec * BARREL_LEN

    def fire(self) -> Projectile | None:
        if self.cooldown > 0:
            return None
        rad = math.radians(self.angle_deg)
        dir_vec = pygame.Vector2(math.cos(rad), -math.sin(rad))
        start_pos = self.barrel_tip()
        proj = Projectile(pos=start_pos, vel=dir_vec * PROJECTILE_SPEED)
        self.cooldown = FIRE_COOLDOWN
        return proj

    def draw(self, surf: pygame.Surface):
        base_rect = pygame.Rect(
            int(self.pivot.x - TURRET_BASE_WIDTH // 2),
            int(self.pivot.y),
            TURRET_BASE_WIDTH,
            TURRET_BASE_HEIGHT,
        )
        pygame.draw.rect(surf, (100, 100, 100), base_rect)
        pygame.draw.rect(
            surf,
            (60, 60, 60),
            (
                0,
                GROUND_Y + TURRET_BASE_HEIGHT,
                WIDTH,
                HEIGHT - (GROUND_Y + TURRET_BASE_HEIGHT),
            ),
        )
        tip = self.barrel_tip()
        pygame.draw.line(
            surf,
            (200, 200, 200),
            (int(self.pivot.x), int(self.pivot.y)),
            (int(tip.x), int(tip.y)),
            6,
        )
        pygame.draw.circle(
            surf,
            (180, 180, 180),
            (int(self.pivot.x), int(self.pivot.y)),
            10,
        )


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Paratrooper")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.big_font = pygame.font.SysFont("consolas", 42, bold=True)

        global HELI_LEVELS
        level_margin_top = 60
        level_margin_between = 70
        candidates = [
            level_margin_top + i * level_margin_between for i in range(3)
        ]
        random.shuffle(candidates)
        HELI_LEVELS = candidates[: random.randint(2, 3)]

        self.joy = None
        self._init_joystick()
        self.reset()

    def _init_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joy = pygame.joystick.Joystick(0)
            self.joy.init()
            print(f"joystick: {self.joy.get_name()}")
        else:
            print(
                "joystick not found: keyboard fallback: "
                "arrows to aim, SPACE to fire"
            )

    def reset(self):
        self.turret = Turret(TURRET_PIVOT)
        self.projectiles: list[Projectile] = []
        self.helicopters: list[Helicopter] = []
        self.troopers: list[Paratrooper] = []
        self.spawn_timer = 0.0
        self.time_to_next_heli = random.uniform(*HELI_SPAWN_EVERY)
        self.score = 0
        self.landed = 0
        self.game_over = False

    def spawn_heli(self):
        level_y = random.choice(HELI_LEVELS)
        direction = random.choice([-1, 1])
        speed = random.uniform(*HELI_SPEED_RANGE)
        x = -HELI_SIZE[0] - 20 if direction > 0 else WIDTH + 20
        heli = Helicopter(
            pos=pygame.Vector2(x, level_y),
            speed=speed,
            direction=direction,
            level_y=level_y,
        )
        self.helicopters.append(heli)

    def handle_input(self, dt: float):
        input_amount = 0.0
        shoot_pressed = False
        if self.joy is not None:
            if self.joy.get_numaxes() > AXIS_INDEX:
                try:
                    input_amount = self.joy.get_axis(AXIS_INDEX)
                except Exception:
                    input_amount = 0.0
            if self.joy.get_numbuttons() > SHOOT_BUTTON_INDEX:
                shoot_pressed = self.joy.get_button(SHOOT_BUTTON_INDEX) == 1
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            input_amount = -1.0
        elif keys[pygame.K_RIGHT]:
            input_amount = 1.0
        if keys[pygame.K_SPACE]:
            shoot_pressed = True
        self.turret.update(dt, input_amount)
        if shoot_pressed:
            proj = self.turret.fire()
            if proj:
                self.projectiles.append(proj)

    def update(self, dt: float):
        if self.game_over:
            return
        self.handle_input(dt)
        self.spawn_timer += dt
        if self.spawn_timer >= self.time_to_next_heli:
            self.spawn_timer = 0.0
            self.time_to_next_heli = random.uniform(*HELI_SPAWN_EVERY)
            self.spawn_heli()
        for h in list(self.helicopters):
            h.update(dt)
            self.troopers.extend(h.maybe_drop(dt))
            if not h.alive:
                self.helicopters.remove(h)
        for p in list(self.projectiles):
            p.update(dt)
            if not p.alive:
                self.projectiles.remove(p)
        for t in list(self.troopers):
            t.update(dt)
            if not t.alive and t.landed:
                self.landed += 1
                self.troopers.remove(t)
                if self.landed >= MAX_LANDED:
                    self.game_over = True

        # collisions: projectile vs paratrooper
        for t in list(self.troopers):
            tr = t.rect()
            for p in list(self.projectiles):
                if tr.colliderect(p.rect()):
                    if t in self.troopers:
                        self.troopers.remove(t)
                    if p in self.projectiles:
                        self.projectiles.remove(p)
                    self.score += 10
                    break

        # collisions: projectile vs helicopter
        for h in list(self.helicopters):
            hr = h.rect()
            for p in list(self.projectiles):
                if hr.colliderect(p.rect()):
                    if h in self.helicopters:
                        self.helicopters.remove(h)
                    if p in self.projectiles:
                        self.projectiles.remove(p)
                    self.score += 50
                    break

    def draw_hud(self, surf: pygame.Surface):
        txt = f"score: {self.score} | landed: {self.landed}/{MAX_LANDED}"
        img = self.font.render(txt, True, (230, 230, 230))
        surf.blit(img, (12, 10))

    def draw(self):
        self.screen.fill((20, 26, 34))
        pygame.draw.rect(self.screen, (24, 30, 40), (0, 0, WIDTH, HEIGHT // 2))
        for h in self.helicopters:
            h.draw(self.screen)
        for t in self.troopers:
            t.draw(self.screen)
        for p in self.projectiles:
            p.draw(self.screen)
        self.turret.draw(self.screen)
        self.draw_hud(self.screen)
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (0, 0))
            msg = "GAME OVER"
            msg2 = "R: Restart | ESC: Quit"
            img = self.big_font.render(msg, True, (255, 220, 220))
            img2 = self.font.render(msg2, True, (240, 240, 240))
            self.screen.blit(
                img,
                (WIDTH // 2 - img.get_width() // 2, HEIGHT // 2 - 60),
            )
            self.screen.blit(
                img2,
                (WIDTH // 2 - img2.get_width() // 2, HEIGHT // 2),
            )
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_r and self.game_over:
                        self.reset()
            if not self.game_over:
                self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()
