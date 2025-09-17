#!/usr/bin/env python

import os
import random

import pygame

pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

count = pygame.joystick.get_count()
if count == 0:
    raise SystemExit(
        "No controller or joystick found. Pair it in System Settings → "
        "Bluetooth (or plug in via USB) and try again."
    )

joystick_name = joystick.get_name()
joystick_id = (
    joystick.get_instance_id() if hasattr(joystick, "get_instance_id") else 0
)

print(f"joystick connected: {joystick_name} (id {joystick_id})")

if not pygame.image.get_extended():
    raise SystemExit("Sorry, extended image module required")


MAX_SHOTS = 2  # most player bullets onscreen
ALIEN_ODDS = 22  # chances a new alien appears
BOMB_ODDS = 60  # chances a new bomb will drop
ALIEN_RELOAD = 12  # frames between new aliens
SCREENRECT = pygame.Rect(0, 0, 640, 480)
SCORE = 0

cwd = os.path.split(os.path.abspath(__file__))[0]


def load_image(file):
    file = os.path.join(cwd, "data", file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit(f'could not load image "{file}" {pygame.get_error()}')
    return surface.convert()


def load_sound(file):
    if not pygame.mixer:
        return None
    file = os.path.join(cwd, "data", file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print(f"error loading {file}")
    return None


class Player(pygame.sprite.Sprite):
    speed = 10
    bounce = 24
    gun_offset = -11
    images: list[pygame.Surface] = []

    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = -1

    def move(self, direction):
        if direction:
            self.facing = direction
        self.rect.move_ip(direction * self.speed, 0)
        self.rect = self.rect.clamp(SCREENRECT)
        if direction < 0:
            self.image = self.images[0]
        elif direction > 0:
            self.image = self.images[1]
        self.rect.top = self.origtop - (self.rect.left // self.bounce % 2)

    def gun_position(self):
        position = self.facing * self.gun_offset + self.rect.centerx
        return position, self.rect.top


class Alien(pygame.sprite.Sprite):
    speed = 13
    animcycle = 12
    images: list[pygame.Surface] = []

    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.facing = random.choice((-1, 1)) * Alien.speed
        self.frame = 0
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self, *args, **kwargs):
        self.rect.move_ip(self.facing, 0)
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing
            self.rect.top = self.rect.bottom + 1
            self.rect = self.rect.clamp(SCREENRECT)
        self.frame = self.frame + 1
        self.image = self.images[self.frame // self.animcycle % 3]


class Explosion(pygame.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images: list[pygame.Surface] = []

    def __init__(self, actor, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife

    def update(self, *args, **kwargs):
        self.life = self.life - 1
        self.image = self.images[self.life // self.animcycle % 2]
        if self.life <= 0:
            self.kill()


class Shot(pygame.sprite.Sprite):
    speed = -11
    images: list[pygame.Surface] = []

    def __init__(self, pos, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self, *args, **kwargs):
        self.rect.move_ip(0, self.speed)
        if self.rect.top <= 0:
            self.kill()


class Bomb(pygame.sprite.Sprite):
    speed = 9
    images: list[pygame.Surface] = []

    def __init__(self, alien, explosion_group, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(
            midbottom=alien.rect.move(0, 5).midbottom
        )
        self.explosion_group = explosion_group

    def update(self, *args, **kwargs):
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom >= 470:
            Explosion(self, self.explosion_group)
            self.kill()


class Score(pygame.sprite.Sprite):
    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.font = pygame.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = "white"
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self, *args, **kwargs):
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = f"Score: {SCORE}"
            self.image = self.font.render(msg, 0, self.color)


def main(window_style=0):
    if pygame.get_sdl_version()[0] == 2:
        pygame.mixer.pre_init(44100, 32, 2, 1024)
    pygame.init()
    if pygame.mixer and not pygame.mixer.get_init():
        print("warning: no sound")
        pygame.mixer = None

    fullscreen = False
    window_style = 0  # | pygame.FULLSCREEN
    depth = pygame.display.mode_ok(SCREENRECT.size, window_style, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, window_style, depth)

    img = load_image("player1.gif")
    Player.images = [img, pygame.transform.flip(img, 1, 0)]
    img = load_image("explosion1.gif")
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]
    Alien.images = [
        load_image(v) for v in ("alien1.gif", "alien2.gif", "alien3.gif")
    ]
    Bomb.images = [load_image("bomb.gif")]
    Shot.images = [load_image("shot.gif")]

    icon = pygame.transform.scale(Alien.images[0], (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption("Aliens")
    pygame.mouse.set_visible(0)

    bgdtile = load_image("background.gif")
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0, 0))
    pygame.display.flip()

    boom_sound = load_sound("boom.wav")
    shoot_sound = load_sound("car_door.wav")
    if pygame.mixer:
        music = os.path.join(cwd, "data", "house_lo.wav")
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)

    aliens = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    all = pygame.sprite.RenderUpdates()
    last_alien = pygame.sprite.GroupSingle()

    alien_reload = ALIEN_RELOAD
    clock = pygame.time.Clock()

    global SCORE
    player = Player(all)
    Alien(aliens, all, last_alien)
    if pygame.font:
        all.add(Score(all))

    while player.alive():
        for event in pygame.event.get():
            if event.type == pygame.QUIT or joystick.get_button(4):
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    if not fullscreen:
                        print("changing to FULLSCREEN")
                        screen_backup = screen.copy()
                        screen = pygame.display.set_mode(
                            SCREENRECT.size,
                            window_style | pygame.FULLSCREEN,
                            depth,
                        )
                        screen.blit(screen_backup, (0, 0))
                    else:
                        print("changing to window mode")
                        screen_backup = screen.copy()
                        screen = pygame.display.set_mode(
                            SCREENRECT.size,
                            window_style,
                            depth,
                        )
                        screen.blit(screen_backup, (0, 0))
                    pygame.display.flip()
                    fullscreen = not fullscreen

        keystate = pygame.key.get_pressed()

        all.clear(screen, background)
        all.update()

        keyboard_direction = keystate[pygame.K_RIGHT] - keystate[pygame.K_LEFT]
        joystick_direction = joystick.get_button(14) - joystick.get_button(13)

        direction = keyboard_direction or joystick_direction

        player.move(direction)
        firing = keystate[pygame.K_SPACE] or joystick.get_button(2)
        if not player.reloading and firing and len(shots) < MAX_SHOTS:
            Shot(player.gun_position(), shots, all)
            if pygame.mixer and shoot_sound is not None:
                shoot_sound.play()

        player.reloading = firing

        if alien_reload:
            alien_reload = alien_reload - 1
        elif not int(random.random() * ALIEN_ODDS):
            Alien(aliens, all, last_alien)
            alien_reload = ALIEN_RELOAD

        if last_alien and not int(random.random() * BOMB_ODDS):
            Bomb(last_alien.sprite, all, bombs, all)

        for alien in pygame.sprite.spritecollide(player, aliens, 1):
            if pygame.mixer and boom_sound is not None:
                boom_sound.play()
            Explosion(alien, all)
            Explosion(player, all)
            SCORE = SCORE + 1
            player.kill()

        for alien in pygame.sprite.groupcollide(aliens, shots, 1, 1).keys():
            if pygame.mixer and boom_sound is not None:
                boom_sound.play()
            Explosion(alien, all)
            SCORE = SCORE + 1

        for bomb in pygame.sprite.spritecollide(player, bombs, 1):
            if pygame.mixer and boom_sound is not None:
                boom_sound.play()
            Explosion(player, all)
            Explosion(bomb, all)
            player.kill()

        dirty = all.draw(screen)
        pygame.display.update(dirty)

        clock.tick(40)

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)
    pygame.time.wait(1000)

    return True


if __name__ == "__main__":
    while main():
        pass

    pygame.quit()
