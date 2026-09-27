# CSE423-Night-at-the-Museum-Haunted-Escape
A Computer Graphics 3D survival-escape game built from scratch in Python and OpenGL. Explore a multi-room museum with ramps, gaps, and spike traps, fight AI enemies with wall-aware pathfinding, collect artifacts, manage stamina and ammo, and disable security to unlock the final escape.

🏛️ Night at the Museum — 3D Haunted Museum Escape

A 3D survival-escape game built from scratch in Python and OpenGL (PyOpenGL/GLUT). Explore a data-driven museum layout, survive enemy AI and environmental traps, manage resources under pressure, and escape before the alarm catches up with you.

<!-- Optional: add a screenshot or GIF here for extra polish ![gameplay screenshot](assets/screenshot.png) -->
📑 Table of Contents
Features
Getting Started
Controls
Tech Stack
🎮 Features
1. Player Movement & Collision System

Move with W/A/S/D while properly interacting with the environment. Walls, closed gates, and boundaries block passage, and the collision system lets the player slide along walls instead of getting stuck.

2. Physics, Gravity, Jump & Terrain Traversal System

The player jumps and falls under gravity while traversing different terrain types, including ramps and floor gaps. Falling into a hole applies damage and returns the player to a safe starting position.

3. Player Health & Damage System

Health can be reduced by enemies, projectiles, traps, lasers, and falls. A shield power-up temporarily blocks incoming damage. Reaching zero health ends the game.

4. Combat System

The player fights back with a limited-ammo weapon. Shots are blocked by walls and closed gates, and reloading is required once ammo runs out. Ghosts return fire with projectiles that travel through the environment and disappear on hitting a wall, the player, or expiring after their lifetime.

5. Enemy AI & Behavior System

Four distinct enemy types, each with its own behavior:

Hunters — actively chase the player
U-Turn enemies — patrol a route and chase once the player is detected
Watchers — freeze when the player looks directly at them
Ghosts — keep their distance and attack with projectiles
6. Data-Driven Museum Layout & Overall Game Drawing System

The museum is generated from predefined layout data — walls, room divisions, gates, floors, and interactive objects are positioned systematically rather than hardcoded per object. The scene draws the museum, player, enemies, artifacts, generators, switches, traps, power-ups, gates, and projectiles each frame, and the player's current room is detected automatically from position.

7. Trap & Trigger System

Pressure plates trigger spikes for a limited duration, while lasers stay active until manually disabled. Both trap types respect the player's shield status.

8. Switch-Based Interaction System

Switches scattered through the museum trigger different effects — disabling lasers or spikes, pausing the alarm, or unlocking areas — updating the relevant game system the moment they're used.

9. Power, Generator & Dynamic Gate System

Generators feed the museum's power and security systems. Gates unlock under different conditions (activating a generator, using a specific switch) and open gradually once unlocked, no longer blocking movement.

10. Alarm & Enemy Aggression System

An active alarm boosts enemy aggression — greater detection range, faster movement — and wakes sleeping enemies. A switch can temporarily suppress the alarm's effect.

11. Temporary Power-Up System

Shield, Speed, and Damage Boost power-ups are active for a limited time after collection, then respawn later so they can be collected again.

12. Proximity Scanner Detection System

Pressing V activates a time-limited scanner that highlights nearby artifacts, generators, switches, power-ups, and enemies — only within its detection range.

13. Sprint & Slip-Hazard System

Sprinting speeds up movement, while slippery hazard zones can trap the player and drain health continuously until they escape the area.

14. Camera Controller System

Three switchable camera modes — First-Person, Third-Person, and Top-Down — each with its own position and viewing angle relative to the player.

15. HUD, Objective & Notification System

The HUD tracks health, current room, camera mode, ammo, generators, and artifacts. The active objective updates automatically as the player progresses, and notifications surface important in-game events.

🚀 Getting Started
Requirements
Python 3.x
PyOpenGL
Installation
bash
pip install PyOpenGL PyOpenGL_accelerate
Run
bash
python museum_full.py
🕹️ Controls
Key / Input	Action
W / A / S / D	Move / Turn
SPACE	Jump
SHIFT	Sprint
E	Interact (generators, switches, artifacts, console, exit)
V	Activate scanner
C	Cycle camera mode (First-Person / Third-Person / Top-Down)
R	Reload weapon
T	Restart game
Left Click	Shoot
Right Click	Cycle camera mode
Arrow Keys	Adjust camera angle / height
🛠️ Tech Stack
Language: Python 3
Graphics: OpenGL via PyOpenGL / GLUT
Architecture: Data-driven layout generation, real-time game loop (idle() → showScreen())
