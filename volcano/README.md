In "example.txt" is a screenshot from a text-based computer game from the 8-bit homebrew computer called Volcano.

The screenshot shows a 64x25-character field.

There is a shape of the volcano with an X character.

"*" represents ashes randomly flying out of the top of the volcano shape. They randomly move up, sideways, and slow down.

On the right, there is a helicopter station drawn with "=" (top) and "!" (sides) symbols.

The helicopter is drawn as:

-+-
 O-+

Or

 -+-
+-O

On the left side of the volcano, there are 4 horizontal segments with people to rescue: "Y" and "I" characters, which flip periodically, representing people waving their hands.

You need to implement this game in Python. Use curses to control the terminal.

A player has 3 lifes (helicopters) - the initial position of the helicopter is on top of the station (on the right), and the remaining helicopters are inside the station (initial 2).

The player controls the helicopter with the arrow keys and fires with the spacebar. The projectiles fire from the helicopter's nose and travel to the edge of the screen. If a projective hits an ash, the ash disappears. If an ash hits the helicopter, it explodes and disappears, so the player begins again from the station if there are helicopters left.

The player must navigate the helicopter over the volcano and avoid collisions with the ash. The player needs to pick up a person and fly them back to the station. To pick up a person, the helicopter needs to fly over the person's character. After that, the person "sticks" to the helicopter as the symbol "I". When the helicopter with the attached person returns to the station, the person "goes" to the station, and the helicopter then flies over the volcano for the next person. The goal is to rescue all 4 with as few helicopters as possible.

Additionally, over time, the lava spreads line by line from the top of the volcano down the slope. Each "spread" is a line "*" drawn from the left point of the volcano profile at a given level to the right.

When the lava hits a level with living humans, the humans die and turn into the flying souls (drawn as "()"). It starts flying randomly like ashes. It cannot be shot, but it can kill the helicopter.

Original game for BBC Micro - https://bbcmicro.co.uk/game.php?id=143
