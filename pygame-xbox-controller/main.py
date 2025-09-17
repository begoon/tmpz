import pygame

print("pygame:", pygame.version.ver)
print("SDL:", pygame.get_sdl_version())

pygame.init()

pygame.joystick.init()

use_controller = False  # TODO(!)

count = pygame.joystick.get_count()
if count == 0:
    raise SystemExit(
        "No controller or joystick found. Pair it in System Settings → "
        "Bluetooth (or plug in via USB) and try again."
    )

joystick = pygame.joystick.Joystick(0)
joystick.init()
joystick_name = joystick.get_name()
joystick_id = (
    joystick.get_instance_id() if hasattr(joystick, "get_instance_id") else 0
)

print(f"connected: {joystick_name} (id {joystick_id})")
screen = pygame.display.set_mode((640, 360))
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Controller events (pygame 2.2+)
        if use_controller:
            if event.type in (
                pygame.CONTROLLERBUTTONDOWN,
                pygame.CONTROLLERBUTTONUP,
                pygame.CONTROLLERAXISMOTION,
                pygame.CONTROLLERTOUCHPADDOWN,
                pygame.CONTROLLERTOUCHPADMOTION,
                pygame.CONTROLLERTOUCHPADUP,
                pygame.CONTROLLERSENSORUPDATE,
                pygame.CONTROLLERDEVICEREMAPPED,
                pygame.CONTROLLERDEVICEADDED,
                pygame.CONTROLLERDEVICEREMOVED,
            ):
                print(event)

        # Joystick events (works on all pygame 2.x)
        if event.type in (
            pygame.JOYBUTTONDOWN,
            pygame.JOYBUTTONUP,
            pygame.JOYAXISMOTION,
            pygame.JOYHATMOTION,
            pygame.JOYDEVICEADDED,
            pygame.JOYDEVICEREMOVED,
        ):
            print(event)

    # Example: poll current state (works with joystick API)
    if not use_controller:
        axes = joystick.get_numaxes()
        buttons = joystick.get_numbuttons()
        hats = joystick.get_numhats()
        # Read some typical controls (indices vary by platform/mapping)
        if axes >= 2:
            lx = joystick.get_axis(0)  # left stick X (-1 left, +1 right)
            ly = joystick.get_axis(1)  # left stick Y (-1 up, +1 down)
            # Triggers are often axes too; try 4 and 5 on SDL mappings
            lt = joystick.get_axis(4) if axes > 4 else 0.0
            rt = joystick.get_axis(5) if axes > 5 else 0.0
            # print(lx, ly, lt, rt)  # uncomment to see continuous values

    pygame.display.flip()
    clock.tick(120)

pygame.quit()
