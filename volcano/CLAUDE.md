# Volcano Rescue Game

Text-based curses game. Single file: `main.py`. Run with `python3 main.py`.
Dependencies: only stdlib (`curses`, `random`, `time`).

## Layout

- **Field**: 64 cols x 25 rows. `example.txt` is the authoritative reference for the exact shape.
- **Volcano**: 'X' outline. Peak cap at row 9 (cols 37-40), slopes widen downward to row 24.
- **Left slope**: has 4 flat platforms (XXXXX, 5 wide) at rows 14, 18, 21, 23.
- **Right slope**: rows 11-20, ends where station begins.
- **Station**: '=' roof at row 16 cols 55-62, '!' walls at cols 55 & 62 rows 17-24.
- **HUD**: row 0, shows lives and rescue count.

## Terrain data

Terrain is hard-coded as exact (col, row) positions in `build_terrain()`, derived from `example.txt`. Lava fill ranges per row are in `LAVA_BOUNDS` dict. When updating the volcano shape, update both `build_terrain()` and `LAVA_BOUNDS` to match.

## Entities (all plain dicts)

| Entity | Keys | Symbol |
|---|---|---|
| Helicopter | x, y (cockpit O), direction (-1/1), carrying, alive | `-+- / +-O` or `-+- / O-+` |
| Person | x, y, alive, rescued, platform_row | Y/I (wave animation) |
| Ash | x, y (float), vx, vy | `*` |
| Soul | x, y (float), vx, vy | `()` |
| Projectile | x, y, dx | `-` |
| Lava | tracked by `lava_level` (int row) | `+` |

## Helicopter sprite

Reference point is cockpit 'O'. Rotor `-+-` always centered on O, one row above.

- **Facing right** (dir=1): `+-O` — tail `+-` left of cockpit
- **Facing left** (dir=-1): `O-+` — tail `-+` right of cockpit
- **Carrying person**: 'I' drawn at (ox, oy+1)
- **Nose** (projectile origin): one cell ahead of O: `(ox + direction, oy)`

## Controls

- Arrow keys: move 1 cell/frame. Left/right: first press turns, second press moves.
- Space: fire projectile in facing direction.
- Q: quit.

## Game loop (~10 FPS)

1. **Input** — non-blocking getch, drain buffer, keep last key
2. **Move heli** — apply movement, clamp to screen, undo if colliding with terrain/station/lava
3. **Respawn** — 1s timer after destruction, then new heli at station (58, 15)
4. **Ashes** — spawn 1 every 6 frames at peak; float physics with gravity (0.025) and horizontal drift; movement multiplied by 0.5; removed if hitting terrain or station
5. **Projectiles** — move 2 cells/frame in dx direction; removed on terrain/station hit
6. **Projectile vs ash** — exact cell match removes both
7. **Ash/soul vs heli** — cell overlap destroys heli, decrements lives
8. **Pickup** — heli cell within 1 Manhattan distance of person
9. **Deposit** — carried person at (ox, oy+1) touching station roof/wall via `cell_in_station()`
10. **Lava** — advances 1 row every 8s from peak (row 9) downward; fills LAVA_BOUNDS inclusive (overwrites terrain X when drawn); kills people when reaching their platform_row, spawns souls
11. **Souls** — float randomly, bounce off screen edges, indestructible
12. **Render** — erase, draw terrain, lava, station (with spare helis), people, ashes, souls, projectiles, active heli, HUD

## Key design decisions

- Lava fills edge-to-edge inclusive (covers X outlines), drawn after terrain.
- Ashes and projectiles cannot penetrate volcano profile or station — removed on contact.
- Person deposit triggers when the hanging person 'I' (oy+1) hits station structure, not the heli itself.
- 3 lives total (1 active + 2 spares shown inside station at cockpit rows 20, 22).
- Game ends: all 4 rescued = win; all lives lost = lose; all people dead/rescued with none carried = lose.
