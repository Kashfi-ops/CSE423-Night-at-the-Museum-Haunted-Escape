# 🏛️ Night at the Museum — 3D Haunted Escape

A 3D survival-escape game built from scratch in Python and OpenGL (PyOpenGL/GLUT). Explore a data-driven museum layout, survive enemy AI and environmental traps, manage resources under pressure, and escape before the alarm catches up with you.

## Description

**Night at the Museum** is a survival-escape game set inside a haunted 3D museum, featuring physics-based movement, jump-and-gravity terrain traversal, and a real health/damage system fed by enemies, traps, and falls. Players restore power through generators, disable a security console under mounting alarm pressure, and navigate spike traps, lasers, and slippery hazards while fending off four distinct enemy types. The game layers in temporary power-ups, a proximity scanner for locating objectives, and switch-triggered systems that reshape the museum as the player progresses. With switchable First-Person, Third-Person, and Top-Down cameras plus a full HUD and objective tracker, it combines tense exploration with reactive, systemic gameplay.

---

## Features & Implementation Details

### Player Mechanics & Physics
*   **Movement & Collision System:** W/A/S/D movement with full environment interaction — walls, closed gates, and boundaries block passage, and the player slides along walls instead of getting stuck.
*   **Physics, Gravity, Jump & Terrain Traversal:** Real gravity and jump velocity across varied terrain, including ramps and floor gaps. Falling into a hole applies damage and resets the player to a safe position.
*   **Health & Damage System:** Health drains from enemies, projectiles, traps, lasers, and falls. A shield power-up temporarily blocks all damage. Reaching zero health ends the game.
*   **Combat System:** Limited-ammo weapon that requires reloading once empty. Shots are blocked by walls and closed gates. Ghosts return fire with projectiles that travel through the environment and disappear on hitting a wall, the player, or expiring after their lifetime.
*   **Sprint & Slip-Hazard System:** Sprinting boosts movement speed. Slippery hazard zones can trap the player, draining health continuously until they escape the area.

### World, Environment & Camera
*   **Data-Driven Museum Layout & Drawing System:** Walls, room divisions, gates, floors, and interactive objects are generated systematically from layout data rather than hardcoded per object. The player's current room is detected automatically from position.
*   **Trap & Trigger System:** Pressure plates activate spikes for a limited duration; lasers stay active until manually disabled. Both trap types respect the player's shield status.
*   **Switch-Based Interaction System:** Switches trigger effects such as disabling lasers or spikes, pausing the alarm, or unlocking areas — updating the relevant game system the moment they're used.
*   **Power, Generator & Dynamic Gate System:** Generators feed the museum's power and security systems. Gates unlock under different conditions (activating a generator, using a specific switch) and open gradually once unlocked.
*   **Camera Systems:** Multiple perspectives including **First-Person**, **Third-Person**, and a fully adjustable **Top-Down** view.

### AI, Hazards & Gameplay Logic
*   **Enemy AI & Behavior System:** Four distinct enemy types, each with its own behavior:
    *   **Hunters** — actively chase the player.
    *   **U-Turn enemies** — patrol a route and chase once the player is detected.
    *   **Watchers** — freeze when the player looks directly at them.
    *   **Ghosts** — keep their distance and attack with projectiles.
*   **Alarm & Enemy Aggression System:** An active alarm boosts enemy aggression — greater detection range, faster movement — and wakes sleeping enemies. A switch can temporarily suppress the alarm's effect.
*   **Temporary Power-Up System:** Shield, Speed, and Damage Boost power-ups are active for a limited time after collection, then respawn later so they can be collected again.
*   **Proximity Scanner Detection System:** Pressing V activates a time-limited scanner that highlights nearby artifacts, generators, switches, power-ups, and enemies within its detection range.
*   **HUD, Objective & Notification System:** The HUD tracks health, current room, camera mode, ammo, generators, and artifacts. The active objective updates automatically as the player progresses, and notifications surface important in-game events.

---

## Controls

| Key | Action |
| :--- | :--- |
| **W / A / S / D** | Move / Turn |
| **SPACE** | Jump |
| **SHIFT** | Sprint |
| **E** | Interact (generators, switches, artifacts, console, exit) |
| **V** | Activate Scanner |
| **C** | Change Camera View |
| **R** | Reload Weapon |
| **T** | Restart Game |
| **Left Click** | Shoot |
| **Right Click** | Change Camera View |
| **Arrow Keys** | Adjust Camera Angle / Height |
