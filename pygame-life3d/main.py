import math
import random
import sys
from collections import defaultdict

import pygame

UNIVERSE_SIZE = 100  # 100x100x100 cube
HALF = UNIVERSE_SIZE // 2

# Ruleset: B6 / S567
BIRTH = {6}
SURVIVE = {5, 6, 7}

SEED_BOX = 50  # size of the random seed cube centered at origin
SEED_PROB = 0.9  # probability of a live cell in the seed cube

SCREEN_W, SCREEN_H = 1200, 800
FOV = 800.0  # perspective factor (larger = more zoomed-in feel)
VOXEL_WORLD_SIZE = 1.0  # world space size of one voxel edge
FACE_GAP_PX = 2  # shrink each face by 2px on screen to create gaps
BG_COLOR = (5, 8, 12)
VOX_COLOR = (60, 200, 255)  # live voxel face color
OUTLINE_COLOR = (0, 0, 0)  # optional outline (disabled by default)
DRAW_OUTLINES = False

AXIS_LEN_MULT = 1.6  # how far the lines extend (in half-extent units)
AXIS_WIDTH = 3  # pixels
AXIS_X_COLOR = (230, 80, 80)  # X = red
AXIS_Y_COLOR = (80, 230, 120)  # Y = green
AXIS_Z_COLOR = (100, 160, 255)  # Z = blue

INITIAL_CAMERA_SCALE = 2.2  # multiplier to ensure full colony is visible
MIN_CAMERA_DIST = 45.0  # clamp so we never go through the scene
MAX_CAMERA_DIST = 1800.0
ROT_SPEED = 1.2  # radians/sec max from full stick deflection
ROLL_SPEED = 1.2  # radians/sec
ZOOM_SPEED = 450.0  # distance units per second

TRIGGER_DEADZONE = 0.12
STICK_DEADZONE = 0.10
ZOOM_DEADZONE = 0.05

# Indices (fallback assumptions; you can change these if your pad differs)
AXIS_LX = 0
AXIS_LY = 1
AXIS_RX = 2
AXIS_RY = 3

AXIS_LT = 4
AXIS_RT = 5

NEIGH_OFFSETS = [
    (dx, dy, dz)
    for dx in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dz in (-1, 0, 1)
    if not (dx == 0 and dy == 0 and dz == 0)
]

CARDINALS = {
    "px": (1, 0, 0),
    "nx": (-1, 0, 0),
    "py": (0, 1, 0),
    "ny": (0, -1, 0),
    "pz": (0, 0, 1),
    "nz": (0, 0, -1),
}


def cube_face_vertices(size):
    s = size / 2.0
    v = {
        "px": [(s, -s, -s), (s, s, -s), (s, s, s), (s, -s, s)],
        "nx": [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)],
        "py": [(-s, s, -s), (-s, s, s), (s, s, s), (s, s, -s)],
        "ny": [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)],
        "pz": [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)],
        "nz": [(-s, -s, -s), (-s, s, -s), (s, s, -s), (s, -s, -s)],
    }
    return v


FACE_VERTS_LOCAL = cube_face_vertices(VOXEL_WORLD_SIZE)


def matmul_vector(m, v):
    x = m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2]
    y = m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2]
    z = m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]
    return (x, y, z)


def rot_x(a):
    ca, sa = math.cos(a), math.sin(a)
    return (
        (1, 0, 0),
        (0, ca, -sa),
        (0, sa, ca),
    )


def rot_y(a):
    ca, sa = math.cos(a), math.sin(a)
    return (
        (ca, 0, sa),
        (0, 1, 0),
        (-sa, 0, ca),
    )


def rot_z(a):
    ca, sa = math.cos(a), math.sin(a)
    return (
        (ca, -sa, 0),
        (sa, ca, 0),
        (0, 0, 1),
    )


def matmul(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def project(point, cam_dist):
    x, y, z = point
    zc = z + cam_dist
    if zc <= 0.01:
        zc = 0.01
    s = FOV / zc
    sx = x * s + SCREEN_W / 2
    sy = -y * s + SCREEN_H / 2
    return (sx, sy, zc)


def shrink_polygon_2d(pts, shrink_px):
    if shrink_px <= 0:
        return pts
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:
        vx, vy = cx - x, cy - y
        d = math.hypot(vx, vy)
        if d > 1e-6:
            nx = x + shrink_px * (vx / d)
            ny = y + shrink_px * (vy / d)
        else:
            nx, ny = x, y
        out.append((nx, ny))
    return out


def step(active):
    neighbor_counts = defaultdict(int)
    for x, y, z in active:
        for dx, dy, dz in NEIGH_OFFSETS:
            nx, ny, nz = x + dx, y + dy, z + dz
            if not (
                0 <= nx < UNIVERSE_SIZE
                and 0 <= ny < UNIVERSE_SIZE
                and 0 <= nz < UNIVERSE_SIZE
            ):
                continue
            neighbor_counts[(nx, ny, nz)] += 1

    new_active = set()
    for cell, n in neighbor_counts.items():
        if cell in active:
            if n in SURVIVE:
                new_active.add(cell)
        else:
            if n in BIRTH:
                new_active.add(cell)
    return new_active


def seed_initial():
    active = set()
    start = HALF - SEED_BOX // 2
    end = start + SEED_BOX
    for x in range(start, end):
        for y in range(start, end):
            for z in range(start, end):
                if random.random() < SEED_PROB:
                    active.add((x, y, z))
    return active


def world_from_cell(ix, iy, iz):
    wx = (ix - HALF + 0.5) * VOXEL_WORLD_SIZE
    wy = (iy - HALF + 0.5) * VOXEL_WORLD_SIZE
    wz = (iz - HALF + 0.5) * VOXEL_WORLD_SIZE
    return (wx, wy, wz)


def render_scene(screen, active, rot_matrix, cam_dist, axis_len_world):
    faces_to_draw = []

    # voxel faces (hidden-surface culling)
    for ix, iy, iz in active:
        cx, cy, cz = world_from_cell(ix, iy, iz)

        for face_key, (dx, dy, dz) in CARDINALS.items():
            nb = (ix + dx, iy + dy, iz + dz)
            if (
                0 <= nb[0] < UNIVERSE_SIZE
                and 0 <= nb[1] < UNIVERSE_SIZE
                and 0 <= nb[2] < UNIVERSE_SIZE
                and nb in active
            ):
                continue  # internal face, invisible

            poly_pts = []
            z_accum = 0.0
            for vx, vy, vz in FACE_VERTS_LOCAL[face_key]:
                wx, wy, wz = cx + vx, cy + vy, cz + vz
                rx, ry, rz = matmul_vector(rot_matrix, (wx, wy, wz))
                sx, sy, zc = project((rx, ry, rz), cam_dist)
                poly_pts.append((sx, sy))
                z_accum += zc

            # backface culling via signed area in screen space
            area = 0.0
            for i in range(4):
                x1, y1 = poly_pts[i]
                x2, y2 = poly_pts[(i + 1) % 4]
                area += x1 * y2 - x2 * y1
            if area <= 0:
                continue

            poly_pts_shrunk = shrink_polygon_2d(poly_pts, FACE_GAP_PX)
            avg_depth = z_accum / 4.0
            faces_to_draw.append((avg_depth, poly_pts_shrunk))

    # sort and draw faces
    faces_to_draw.sort(key=lambda t: -t[0])  # far to near
    for _, poly in faces_to_draw:
        pygame.draw.polygon(screen, VOX_COLOR, poly)
        if DRAW_OUTLINES:
            pygame.draw.polygon(screen, OUTLINE_COLOR, poly, 1)

    # axis guide lines from origin
    # Build endpoints in world space: origin -> unit axis * axis_len_world
    axes = [
        ((0.0, 0.0, 0.0), (axis_len_world, 0.0, 0.0), AXIS_X_COLOR),  # X
        ((0.0, 0.0, 0.0), (0.0, axis_len_world, 0.0), AXIS_Y_COLOR),  # Y
        ((0.0, 0.0, 0.0), (0.0, 0.0, axis_len_world), AXIS_Z_COLOR),  # Z
    ]

    for p0, p1, color in axes:
        r0 = matmul_vector(rot_matrix, p0)
        r1 = matmul_vector(rot_matrix, p1)
        s0x, s0y, _ = project(r0, cam_dist)
        s1x, s1y, _ = project(r1, cam_dist)
        pygame.draw.line(screen, color, (s0x, s0y), (s1x, s1y), AXIS_WIDTH)


def deadzone(v, threshold) -> float:
    return 0.0 if abs(v) < threshold else v


def normalize_trigger_0_1(v) -> float:
    """
    Accepts raw axis in 0..1 or -1..1 (with -1 = released).
    Returns 0..1 with deadzone applied.
    """
    if v < -0.001:  # typical -1..1 mapping
        v = (v + 1.0) / 2.0
    v = max(0.0, min(1.0, v))
    return 0.0 if v < TRIGGER_DEADZONE else v


def read_joystick_axes(joystick):
    num_axes = joystick.get_numaxes()

    lx = joystick.get_axis(AXIS_LX) if num_axes > AXIS_LX else 0.0
    ly = joystick.get_axis(AXIS_LY) if num_axes > AXIS_LY else 0.0
    rx = joystick.get_axis(AXIS_RX) if num_axes > AXIS_RX else 0.0

    lx = deadzone(lx, STICK_DEADZONE)
    ly = deadzone(ly, STICK_DEADZONE)
    rx = deadzone(rx, STICK_DEADZONE)

    lt = normalize_trigger_0_1(joystick.get_axis(AXIS_LT))
    rt = normalize_trigger_0_1(joystick.get_axis(AXIS_RT))

    return lx, ly, rx, lt, rt


BUTTON_A = 0  # pause/unpause
BUTTON_B = 1  # step
BUTTON_X = 2  # restart
BUTTON_Y = 3  # quit


def main_loop():
    pygame.init()
    pygame.display.set_caption("3D Game of Life (B6/S567)")
    screen = pygame.display.set_mode(
        (SCREEN_W, SCREEN_H),
        pygame.SCALED | pygame.RESIZABLE,
    )
    clock = pygame.time.Clock()

    pygame.joystick.init()
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"joystick: {joystick.get_name()} axes={joystick.get_numaxes()}")
    else:
        print("no gamepad found — keyboard fallback enabled")

    random.seed(3)
    active = seed_initial()
    paused = False

    # camera
    half_extent = (UNIVERSE_SIZE * VOXEL_WORLD_SIZE) / 2.0
    cam_dist = max(MIN_CAMERA_DIST, INITIAL_CAMERA_SCALE * half_extent * 3.0)
    axis_len_world = AXIS_LEN_MULT * half_extent

    # rotations
    pitch = 0.5  # X rotation
    yaw = 0.7  # Y rotation
    roll = 0.0  # Z rotation

    # timing for stepping
    step_cooldown = 0.0
    STEP_INTERVAL = 0.5  # seconds between auto-steps when unpaused

    running = True
    terminate = False
    while running:
        ticker = clock.tick(60) / 1000.0
        step_cooldown -= ticker

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                terminate = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_PERIOD and paused:
                    active = step(active)
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == BUTTON_X or event.button == BUTTON_Y:
                    running = False
                    terminate = event.button == BUTTON_Y
                elif event.button == BUTTON_A:
                    paused = not paused
                elif event.button == BUTTON_B and paused:
                    active = step(active)

        if joystick:
            lx, ly, rx, lt, rt = read_joystick_axes(joystick)
        else:
            keys = pygame.key.get_pressed()
            lx = (-1.0 if keys[pygame.K_a] else 0.0) + (
                1.0 if keys[pygame.K_d] else 0.0
            )
            ly = (-1.0 if keys[pygame.K_w] else 0.0) + (
                1.0 if keys[pygame.K_s] else 0.0
            )
            rx = (-1.0 if keys[pygame.K_q] else 0.0) + (
                1.0 if keys[pygame.K_e] else 0.0
            )
            lt = 1.0 if keys[pygame.K_z] else 0.0
            rt = 1.0 if keys[pygame.K_x] else 0.0

        # push stick up (negative ly) -> pitch down
        pitch += -ly * ROT_SPEED * ticker
        yaw += lx * ROT_SPEED * ticker

        # right stick X controls roll; right Y is ignored
        roll += rx * ROLL_SPEED * ticker

        zoom_input = lt - rt
        if abs(zoom_input) < ZOOM_DEADZONE:
            zoom_input = 0.0

        cam_dist += zoom_input * ZOOM_SPEED * ticker
        cam_dist = max(MIN_CAMERA_DIST, min(MAX_CAMERA_DIST, cam_dist))

        # compose rotation matrix: Rz * Ry * Rx
        R = rot_z(roll)
        R = matmul(R, rot_y(yaw))
        R = matmul(R, rot_x(pitch))

        # step simulation
        if not paused and step_cooldown <= 0.0:
            active = step(active)
            step_cooldown = STEP_INTERVAL

        screen.fill(BG_COLOR)
        render_scene(screen, active, R, cam_dist, axis_len_world)

        font = pygame.font.SysFont(None, 20)
        text = (
            f"B6 / S567 | live:{len(active)} | cam:{cam_dist:.0f} | "
            f"pitch:{pitch:.2f} yaw:{yaw:.2f} roll:{roll:.2f} "
            f"{'| PAUSED' if paused else ''}"
        ).upper()
        screen.blit(font.render(text, True, (200, 200, 200)), (10, 8))

        pygame.display.flip()

    pygame.quit()

    if terminate:
        sys.exit(0)


if __name__ == "__main__":
    while True:
        main_loop()
