from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# =====================================================================
# WORLD LAYOUT
#   
# =====================================================================

X0, X1 = -300, 300
Y_MAIN0 = -100
Y_G1 = 300     # Main Hall / Ancient Gallery gate
Y_G2 = 600     # Ancient / Royal gate      (unlocks after generator 1)
Y_G3 = 900     # Royal / Science gate      (unlocks after generator 2)
Y_G4 = 1200    # Science / Security gate   (unlocks after generator 3 / power restored)
Y_G5 = 1500    # Security / Final gate     (unlocks after security disabled)
Y_END = 1800   # far wall of final escape area
EXIT_Y = 1770  # crossing this triggers WIN

ROOMS = [
    ("Main Hall",        Y_MAIN0, Y_G1, (0.10, 0.10, 0.15)),
    ("Ancient Gallery",  Y_G1,    Y_G2, (0.17, 0.14, 0.09)),
    ("Royal Gallery",    Y_G2,    Y_G3, (0.18, 0.13, 0.04)),
    ("Science Gallery",  Y_G3,    Y_G4, (0.05, 0.14, 0.17)),
    ("Security Room",    Y_G4,    Y_G5, (0.20, 0.05, 0.05)),
    ("Final Escape Area",Y_G5,    Y_END,(0.14, 0.10, 0.20)),
]

GATE_WIDTH = 150

# locked / unlock_condition keys resolved each frame in update_gates()
GATES = [
    {"y": Y_G1, "locked": True,  "condition": "switchA",   "open_progress": 0.0, "slip_added": False},
    {"y": Y_G2, "locked": True,  "condition": "gen1",       "open_progress": 0.0, "slip_added": False},
    {"y": Y_G3, "locked": True,  "condition": "gen2",       "open_progress": 0.0, "slip_added": False},
    {"y": Y_G4, "locked": True,  "condition": "gen3",       "open_progress": 0.0, "slip_added": False},
    {"y": Y_G5, "locked": True,  "condition": "security",   "open_progress": 0.0, "slip_added": False},
]

# Static perimeter + divider + decorative walls: (cx, cy, half_w, half_d, height)
WALLS = []

def _add_perimeter_and_dividers():
    mid_y = (Y_MAIN0 + Y_END) / 2
    half_len = (Y_END - Y_MAIN0) / 2 + 40
    WALLS.append((X0 - 20, mid_y, 20, half_len, 220))   # left wall
    WALLS.append((X1 + 20, mid_y, 20, half_len, 220))   # right wall
    WALLS.append((0, Y_MAIN0 - 30, X1 - X0, 20, 220))   # back wall

    for gy in (Y_G1, Y_G2, Y_G3, Y_G4, Y_G5):
        half_gap = GATE_WIDTH / 2
        left_w = (gy - X0) - half_gap   # unused helper, kept simple below
        # left stub
        seg_w = (X1 - X0 - GATE_WIDTH) / 2
        WALLS.append((X0 + seg_w / 2, gy, seg_w / 2, 15, 220))
        WALLS.append((X1 - seg_w / 2, gy, seg_w / 2, 15, 220))

_add_perimeter_and_dividers()

# Room-specific obstacle / cover walls (also drive U-turn enemy navigation)
WALLS += [
    (-120, 450, 18, 60, 150),     # Ancient Gallery vertical wall (was a horizontal "broken pillar" wall)
    (0, 760, 130, 22, 160),       # Royal Gallery blocking wall (forces U-turn to reach generator 2)
    (-160, 1050, 18, 90, 150),    # Science Gallery lab wall
    (100, 1350, 90, 18, 150),     # Security Room console cover wall
]

HOLES = [
    (0, 380, 30, 24),             # Ancient Gallery floor gap (jumpable) - CHANGED: smaller (was 55, 45)
]

RAMP = (150, 470, 250, 470, 0, 55)   # Ancient Gallery ramp up to a ledge

SLIP_ZONES = [
    (-150, 470, 90, 55),          # Ancient Gallery - polished stone floor
    (120, 700, 80, 70),           # Royal Gallery - reflecting pool
    (-100, 1350, 80, 70),         # Security Room - waxed floor during alarm
]
BASE_SLIP_ZONES = list(SLIP_ZONES)

# =====================================================================
# ARTIFACTS / GENERATORS / SWITCHES / TRAPS / POWER-UPS
# =====================================================================

ARTIFACTS = [
    {"name": "Ancient Mask",       "x": -220, "y": 400, "collected": False},
    {"name": "Ancient Painting",   "x": 220,  "y": 550, "collected": False},
    {"name": "Royal Crown",        "x": -180, "y": 820, "collected": False},
    {"name": "Golden Statue",      "x": 200,  "y": 620, "collected": False},
    {"name": "Mysterious Crystal", "x": 0,    "y": 1130, "collected": False},
]

GENERATORS = [
    {"id": 1, "x": 0,    "y": 480,  "active": False},   # Ancient Gallery - simple interact
    {"id": 2, "x": 0,    "y": 830,  "active": False},   # Royal Gallery - behind trap corridor
    {"id": 3, "x": -160, "y": 1120, "active": False},   # Science Gallery - guarded by enemies
]

SWITCHES = [
    {"id": "A", "x": 260, "y": 150,  "used": False, "fn": "vault"},
    {"id": "B", "x": 160, "y": 1000, "used": False, "fn": "laser_off"},
    {"id": "C", "x": -60, "y": 700,  "used": False, "fn": "spikes_off"},
    {"id": "D", "x": 60,  "y": 1300, "used": False, "fn": "alarm_pause"},
]

PRESSURE_PLATE = {"x": 0, "y": 700, "triggered_timer": 0.0}
SPIKES = {"x": 0, "y": 750, "hw": 60, "hd": 40, "active": False, "disabled": False}

LASER = {"x0": -260, "y": 1000, "x1": -60, "z": 45, "active": True, "disabled": False}

# Power-up pickup colors (shield/speed/damage), distinguishable from the gold artifacts
POWERUPS = [
    {"type": "shield", "x": 250, "y": 250, "color": (0.25, 0.55, 1.0), "alive": True, "respawn": 0.0},
    {"type": "speed",  "x": -100, "y": 900, "color": (0.2, 0.85, 1.0), "alive": True, "respawn": 0.0},
    {"type": "damage", "x": 120, "y": 1400, "color": (0.1, 0.35, 0.95), "alive": True, "respawn": 0.0},
]

SECURITY_CONSOLE = {"x": 0, "y": 1340}

# =====================================================================
# ENEMIES
# =====================================================================

ENEMIES = [
    {"id": 1, "type": "hunter", "x": 0, "y": 500, "z": 40, "health": 10, "max_health": 10,
     "speed": 70, "state": "PATROL", "room_y": (Y_G1, Y_G2),
     "waypoints": [(-150, 500), (150, 500)], "wp_index": 0},

    {"id": 2, "type": "uturn", "x": 0, "y": 650, "z": 40, "health": 10, "max_health": 10,
     "speed": 75, "state": "PATROL", "room_y": (Y_G2, Y_G3),
     "waypoints": [(-180, 700), (-180, 830), (180, 830), (180, 700)], "wp_index": 0},

    {"id": 3, "type": "watcher", "x": 150, "y": 850, "z": 40, "health": 20, "max_health": 20,
     "speed": 55, "state": "IDLE", "room_y": (Y_G2, Y_G3), "waypoints": [], "wp_index": 0},

    {"id": 4, "type": "ghost", "x": 100, "y": 1100, "z": 60, "health": 10, "max_health": 10,
     "speed": 65, "state": "IDLE", "room_y": (Y_G3, Y_G4), "waypoints": [], "wp_index": 0,
     "attack_cd": 0.0, "preferred_range": 220},

    {"id": 5, "type": "hunter", "x": -100, "y": 1350, "z": 40, "health": 10, "max_health": 10,
     "speed": 90, "state": "IDLE", "room_y": (Y_G4, Y_G5), "waypoints": [], "wp_index": 0,
     "asleep_until_alarm": True},

    {"id": 6, "type": "ghost", "x": 100, "y": 1400, "z": 60, "health": 20, "max_health": 20,
     "speed": 70, "state": "IDLE", "room_y": (Y_G4, Y_G5), "waypoints": [], "wp_index": 0,
     "attack_cd": 0.0, "preferred_range": 200, "asleep_until_alarm": True},
]

GHOST_PROJECTILES = []   # {x,y,z,vx,vy,life}
BULLET_TRAILS = []       # {x0,y0,z0,x1,y1,z1,life}  purely visual tracers

# =====================================================================
# GAME / PLAYER STATE
# =====================================================================

player = {
    "x": 0.0, "y": Y_MAIN0 + 40, "z": 0.0, "vz": 0.0, "angle": 90.0,
    "is_jumping": False,
    "health": 100.0, "max_health": 100.0,
    "stamina": 100.0, "max_stamina": 100.0,
    "sprinting": False,
    "shield_timer": 0.0, "speed_timer": 0.0, "damage_timer": 0.0,
    "ammo_loaded": 6, "ammo_reserve": 24, "reloading": False, "reload_timer": 0.0,
    "in_slip_zone": False, "slip_flash": 0.0,
    "scanner_timer": 0.0,
}

MOVE_SPEED = 165.0
SPRINT_MULT = 1.85
SPEED_POWERUP_MULT = 1.4
JUMP_FORCE = 340.0
GRAVITY = 900.0
PLAYER_RADIUS = 22.0

SPRINT_DRAIN_RATE = 22.0
STAMINA_REGEN_RATE = 14.0
ZONE_WALK_DRAIN_RATE = 45.0
ZONE_SPRINT_DRAIN_RATE = 30.0
SLIP_CHANCE_PER_SEC = 0.9
SLIP_DAMAGE = 14.0

SCANNER_RANGE = 260.0
SCANNER_DURATION = 4.0

# Gun placement (shared by draw_player_model() and gun_muzzle_world())
GUN_LOCAL_OFFSET_FP = (18, -10, 58)   # first-person hand offset
GUN_LOCAL_OFFSET_TP = (20, -14, 53)   # third-person / top-down hand offset
GUN_MUZZLE_FORWARD = 15 + 14          # gun-body forward offset + barrel length = muzzle tip

camera_mode = "THIRD_PERSON"
camera_orbit = 0.0
camera_height_offset = 0.0


KEY_HOLD_TIMEOUT = 0.2
key_last_seen = {}      # key (bytes) -> time.time() of its most recent keydown
sprint_last_seen = 0.0  # time.time() of the most recent SHIFT+movement keydown

messages = []
game_over = False
game_won = False
power_restored = False
security_active = False
security_disabled = False
alarm_active = False
alarm_pause_timer = 0.0
shutdown_active = False
shutdown_progress = 0.0

last_time = time.time()
prev_health = player["health"]
damage_flash_timer = 0.0
damage_popup_timer = 0.0
damage_popup_amount = 0
prev_ammo_loaded = player["ammo_loaded"]
prev_ammo_reserve = player["ammo_reserve"]
prev_objective = ""

# =====================================================================
# HELPERS
# =====================================================================

def add_message(text, duration=2.5):
    messages.append([text, duration])
    print(text)


def dist2(ax, ay, bx, by):
    return (ax - bx) ** 2 + (ay - by) ** 2


def point_in_rect(px, py, cx, cy, hw, hd):
    return (cx - hw) <= px <= (cx + hw) and (cy - hd) <= py <= (cy + hd)


def circle_rect_collides(px, py, r, cx, cy, hw, hd):
    nx = max(cx - hw, min(px, cx + hw))
    ny = max(cy - hd, min(py, cy + hd))
    dx, dy = px - nx, py - ny
    return (dx * dx + dy * dy) < (r * r)


def gate_wall_box(gate):
    
    half_gap = GATE_WIDTH / 2
    return (0, gate["y"], half_gap, 15, 200 * (1.0 - gate["open_progress"]))


def check_wall_collision(nx, ny):
    for (cx, cy, hw, hd, _h) in WALLS:
        if circle_rect_collides(nx, ny, PLAYER_RADIUS, cx, cy, hw, hd):
            return True
    for gate in GATES:
        if gate["open_progress"] < 0.9:
            cx, cy, hw, hd, _h = gate_wall_box(gate)
            if circle_rect_collides(nx, ny, PLAYER_RADIUS, cx, cy, hw, hd):
                return True
    if not SPIKES["disabled"] and SPIKES["active"]:
        pass  # spikes don't block movement, they damage on contact (handled elsewhere)
    return False


def in_hole(px, py):
    for (cx, cy, hw, hd) in HOLES:
        if point_in_rect(px, py, cx, cy, hw, hd):
            return True
    return False


def in_slip_zone(px, py):
    for (cx, cy, hw, hd) in SLIP_ZONES:
        if point_in_rect(px, py, cx, cy, hw, hd):
            return True
    return False


def ground_height(px, py):
    x1, y1, x2, y2, z0, z1 = RAMP
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    if point_in_rect(px, py, cx, cy, abs(x2 - x1) / 2 + 30, abs(y2 - y1) / 2 + 30):
        t = max(0.0, min(1.0, (px - x1) / (x2 - x1 if x2 != x1 else 1)))
        return z0 + t * (z1 - z0)
    return 0.0


def check_entity_wall_collision(nx, ny, radius):
    for (cx, cy, hw, hd, _h) in WALLS:
        if circle_rect_collides(nx, ny, radius, cx, cy, hw, hd):
            return True
    for gate in GATES:
        if gate["open_progress"] < 0.9:
            cx, cy, hw, hd, _h = gate_wall_box(gate)
            if circle_rect_collides(nx, ny, radius, cx, cy, hw, hd):
                return True
    return False


ENEMY_RADIUS = 26.0


def try_move_entity(e, dx, dy, radius=ENEMY_RADIUS):
    
    nx = max(X0 + radius, min(X1 - radius, e["x"] + dx))
    if not check_entity_wall_collision(nx, e["y"], radius):
        e["x"] = nx
    ny = max(Y_MAIN0 + radius, min(Y_END - radius, e["y"] + dy))
    if not check_entity_wall_collision(e["x"], ny, radius):
        e["y"] = ny


def get_current_objective():
    if game_won:
        return "Escaped! You win."
    if GATES[0]["locked"]:
        return "Find Switch A in the Main Hall to unlock the vault door"
    if not GENERATORS[0]["active"]:
        return "Find & activate Generator 1 (Ancient Gallery)"
    if not GENERATORS[1]["active"]:
        return "Find & activate Generator 2 (Royal Gallery)"
    if not GENERATORS[2]["active"]:
        return "Find & activate Generator 3 (Science Gallery)"
    if not security_disabled:
        return "Reach the Security Console and disable security"
    return "Sprint to the Final Exit!"


def line_of_sight_blocked(x0, y0, x1, y1):
    steps = 8
    for i in range(1, steps):
        t = i / steps
        px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for (cx, cy, hw, hd, _h) in WALLS:
            if point_in_rect(px, py, cx, cy, hw, hd):
                return True
       
        for gate in GATES:
            if gate["open_progress"] < 0.9:
                gcx, gcy, ghw, ghd, _gh = gate_wall_box(gate)
                if point_in_rect(px, py, gcx, gcy, ghw, ghd):
                    return True
    return False


def get_current_room():
    for (name, y0, y1, _color) in ROOMS:
        if y0 <= player["y"] < y1:
            return name
    return ROOMS[-1][0] if player["y"] >= ROOMS[-1][1] else ROOMS[0][0]


def scanner_glow(x, y, color):
    
    if player["scanner_timer"] <= 0:
        return
    if dist2(player["x"], player["y"], x, y) > SCANNER_RANGE ** 2:
        return
    glPushMatrix()
    glTranslatef(x, y, 70)
    glColor3f(*color)  #glow kore
    gluSphere(gluNewQuadric(), 10, 8, 8)
    glPopMatrix()

# =====================================================================
# TEXT / HUD
# =====================================================================

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def bar(x, y, w, h, pct, color):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.15, 0.15, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(x, y); glVertex2f(x + w, y)
    glVertex2f(x + w, y + h); glVertex2f(x, y + h)
    glEnd()

    glColor3f(*color)
    fw = max(0.0, w * max(0.0, pct))
    glBegin(GL_QUADS)
    glVertex2f(x, y); glVertex2f(x + fw, y)
    glVertex2f(x + fw, y + h); glVertex2f(x, y + h)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud():
    
    collected = sum(1 for a in ARTIFACTS if a["collected"])
    generators_active = sum(1 for g in GENERATORS if g["active"])

    reload_text = "RELOADING..." if player["reloading"] else "READY"
    reload_color = (1.0, 0.6, 0.2) if player["reloading"] else (0.6, 1.0, 0.6)

    draw_text(10, 770, f"ROOM: {get_current_room()}")
    draw_text(10, 744, f"HP: {int(round(player['health']))} / {int(player['max_health'])}")
    draw_text(10, 718, f"CAMERA: {camera_mode}")
    draw_text(10, 692, f"GENERATORS: {generators_active} / {len(GENERATORS)}")
    draw_text(10, 666, f"ARTIFACTS: {collected} / {len(ARTIFACTS)}")
    draw_text(10, 640, f"AMMO: {player['ammo_loaded']} / {player['ammo_reserve']}")
    draw_text(160, 640, f"RELOAD: {reload_text}", color=reload_color)
    draw_text(10, 614, f"OBJECTIVE: {get_current_objective()}", color=(1.0, 0.85, 0.4))

    # Temporary event notifications 
    notice_y = 580
    for i, (text, _remaining) in enumerate(messages[-3:][::-1]):
        draw_text(10, notice_y - i * 26, text, color=(0.4, 1.0, 0.6))

    if game_over:
        draw_text(400, 400, "GAME OVER - press T to restart", color=(1, 0.2, 0.2))
    if game_won:
        draw_text(380, 400, "MUSEUM ESCAPED - YOU WIN! (T to restart)", color=(0.3, 1.0, 0.4))

# =====================================================================
# WORLD DRAWING
# =====================================================================

def draw_floor():
    for (_name, y0, y1, color) in ROOMS:
        c = color
        if alarm_active:
            c = (min(1, color[0] + 0.15), color[1], color[2])
        glColor3f(*c)
        glBegin(GL_QUADS)
        glVertex3f(X0, y0, 0)
        glVertex3f(X1, y0, 0)
        glVertex3f(X1, y1, 0)
        glVertex3f(X0, y1, 0)
        glEnd()

    glColor3f(0, 0, 0)
    for (cx, cy, hw, hd) in HOLES:
        glBegin(GL_QUADS)
        glVertex3f(cx - hw, cy - hd, 0.5); glVertex3f(cx + hw, cy - hd, 0.5)
        glVertex3f(cx + hw, cy + hd, 0.5); glVertex3f(cx - hw, cy + hd, 0.5)
        glEnd()

    glColor3f(0.55, 0.15, 0.6)
    for (cx, cy, hw, hd) in SLIP_ZONES:
        glBegin(GL_QUADS)
        glVertex3f(cx - hw, cy - hd, 0.4); glVertex3f(cx + hw, cy - hd, 0.4)
        glVertex3f(cx + hw, cy + hd, 0.4); glVertex3f(cx - hw, cy + hd, 0.4)
        glEnd()

    x1, y1, x2, y2, z0, z1 = RAMP
    glColor3f(0.3, 0.3, 0.4)
    glBegin(GL_QUADS)
    glVertex3f(x1, y1 - 60, z0); glVertex3f(x2, y2 - 60, z1)
    glVertex3f(x2, y2 + 60, z1); glVertex3f(x1, y1 + 60, z0)
    glEnd()

    # pressure plate
    glColor3f(0.5, 0.5, 0.15) if PRESSURE_PLATE["triggered_timer"] <= 0 else glColor3f(0.9, 0.7, 0.1)
    px, py = PRESSURE_PLATE["x"], PRESSURE_PLATE["y"]
    glBegin(GL_QUADS)
    glVertex3f(px - 35, py - 35, 1); glVertex3f(px + 35, py - 35, 1)
    glVertex3f(px + 35, py + 35, 1); glVertex3f(px - 35, py + 35, 1)
    glEnd()


def draw_wall(cx, cy, hw, hd, h):
    if h <= 1:
        return
    glPushMatrix()
    glTranslatef(cx, cy, h / 2)
    glColor3f(0.22, 0.22, 0.3)
    glScalef(hw * 2, hd * 2, h)
    glutSolidCube(1)
    glPopMatrix()


def draw_room():
    for (cx, cy, hw, hd, h) in WALLS:
        draw_wall(cx, cy, hw, hd, h)


def draw_gate(gate):
    cx, cy, hw, hd, h = gate_wall_box(gate)
    if h <= 1:
        return
    glPushMatrix()
    glTranslatef(cx, cy, h / 2 + gate["open_progress"] * 220)
    glColor3f(0.75, 0.55, 0.15) if gate["open_progress"] < 1 else glColor3f(0.3, 0.5, 0.3)
    glScalef(hw * 2, hd * 2, h)
    glutSolidCube(1)
    glPopMatrix()


def draw_artifact_obj(a):
    if a["collected"]:
        return
    scanner_glow(a["x"], a["y"], (1.0, 0.85, 0.2))
    glPushMatrix()
    glTranslatef(a["x"], a["y"], 30 + 8 * math.sin(time.time() * 2))
    glRotatef(time.time() * 40 % 360, 0, 0, 1)
    glColor3f(1.0, 0.85, 0.2)
    # Crystal/diamond silhouette: two tapered cylinders joined base-to-base
    quad = gluNewQuadric()
    gluCylinder(quad, 14, 0.5, 19, 8, 2)
    glPushMatrix()
    glRotatef(180, 1, 0, 0)
    gluCylinder(quad, 14, 0.5, 19, 8, 2)
    glPopMatrix()
    glPopMatrix()


def draw_generator_obj(g):
    scanner_glow(g["x"], g["y"], (0.2, 1.0, 0.3))
    active_color = (0.2, 1.0, 0.3)
    idle_color = (0.35, 0.3, 0.15)
    color = active_color if g["active"] else idle_color

    glPushMatrix()
    glTranslatef(g["x"], g["y"], 0)
    glColor3f(*color)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)   # stand the cylinder upright (+Z)
    quad = gluNewQuadric()
    gluCylinder(quad, 20, 20, 55, 12, 4)
    glPopMatrix()

    # top cap
    glPushMatrix()
    glTranslatef(0, 0, 55)
    glColor3f(min(1.0, color[0] + 0.15), min(1.0, color[1] + 0.15), min(1.0, color[2] + 0.15))
    gluSphere(gluNewQuadric(), 20, 10, 10)
    glPopMatrix()

    # small side vent
    glPushMatrix()
    glTranslatef(22, 0, 30)
    glColor3f(0.15, 0.15, 0.15)
    glScalef(10, 10, 30)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()


def draw_switch_obj(sw):
    scanner_glow(sw["x"], sw["y"], (0.2, 0.4, 1.0))
    base_color = (0.15, 0.15, 0.2) if sw["used"] else (0.15, 0.25, 0.5)
    lever_color = (0.25, 0.25, 0.3) if sw["used"] else (0.2, 0.45, 1.0)

    glPushMatrix()
    glTranslatef(sw["x"], sw["y"], 0)

    # rectangular base plate
    glPushMatrix()
    glTranslatef(0, 0, 8)
    glColor3f(*base_color)
    glScalef(26, 16, 16)
    glutSolidCube(1)
    glPopMatrix()

    # lever arm - tilts when used
    glPushMatrix()
    glTranslatef(0, 0, 16)
    glRotatef(55 if sw["used"] else -20, 0, 1, 0)
    glColor3f(*lever_color)
    glTranslatef(0, 0, 14)
    glScalef(6, 6, 28)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()


def draw_spike_trap():
    if SPIKES["disabled"]:
        return
    n = 4
    h = 45 if SPIKES["active"] else 4
    for i in range(n):
        sx = SPIKES["x"] - SPIKES["hw"] + (i + 0.5) * (2 * SPIKES["hw"] / n)
        glPushMatrix()
        glTranslatef(sx, SPIKES["y"], h / 2)
        glColor3f(0.7, 0.7, 0.75)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 10, 0.5, h, 8, 2)
        glPopMatrix()


def draw_laser_trap():
    if LASER["disabled"] or not LASER["active"]:
        return
    glColor3f(1.0, 0.1, 0.1)
    glLineWidth(4)
    glBegin(GL_LINES)
    glVertex3f(LASER["x0"], LASER["y"], LASER["z"])
    glVertex3f(LASER["x1"], LASER["y"], LASER["z"])
    glEnd()


def draw_powerup_obj(pu):
    if not pu["alive"]:
        return
    scanner_glow(pu["x"], pu["y"], pu["color"])
    bob = 30 + 6 * math.sin(time.time() * 3)
    spin = (time.time() * 90) % 360

    glPushMatrix()
    glTranslatef(pu["x"], pu["y"], bob)
    glRotatef(spin, 0, 0, 1)
    glColor3f(*pu["color"])

    if pu["type"] == "shield":
        gluSphere(gluNewQuadric(), 16, 10, 10)   # glowing orb
    elif pu["type"] == "speed":
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 10, 0.5, 30, 8, 2)
        glPushMatrix()
        glTranslatef(0, 0, -14)
        gluCylinder(gluNewQuadric(), 14, 0.5, 14, 8, 2)
        glPopMatrix()
    else:
        # damage boost - 
        

        glPushMatrix()
        glScalef(9.0, 9.0, 9.0)
        glutSolidCube(1)
        glPopMatrix()
        # (translate x, y, z, rotate-about-X, rotate-about-Y) for each spike
        # so it points straight out from the core along that axis
        spikes = [
            (14, 0, 0, 0, 90), (-14, 0, 0, 0, -90),
            (0, 14, 0, -90, 0), (0, -14, 0, 90, 0),
            (0, 0, 14, 0, 0), (0, 0, -14, 180, 0),
        ]
        for (tx, ty, tz, rx, ry) in spikes:
            glPushMatrix()
            glTranslatef(tx, ty, tz)
            glRotatef(rx, 1, 0, 0)
            glRotatef(ry, 0, 1, 0)
            gluCylinder(gluNewQuadric(), 5, 0.3, 12, 6, 2)
            glPopMatrix()

    glPopMatrix()


def draw_security_console():
    active_alert = security_active and not security_disabled
    body_color = (0.18, 0.2, 0.24)

    glPushMatrix()
    glTranslatef(SECURITY_CONSOLE["x"], SECURITY_CONSOLE["y"], 0)

    # main console body
    glPushMatrix()
    glTranslatef(0, 0, 30)
    glColor3f(*body_color)
    glScalef(70, 40, 60)
    glutSolidCube(1)
    glPopMatrix()

    # angled screen
    glPushMatrix()
    glTranslatef(0, -18, 55)
    glRotatef(-25, 1, 0, 0)
    glColor3f(0.9, 0.15, 0.15) if active_alert else glColor3f(0.2, 0.7, 0.3)
    glScalef(55, 4, 26)
    glutSolidCube(1)
    glPopMatrix()

    # indicator lights along the front
    for i in range(3):
        glPushMatrix()
        glTranslatef(-20 + i * 20, -22, 40)
        blink = (math.sin(time.time() * 6 + i) > 0) if active_alert else True
        if active_alert and blink:
            glColor3f(1.0, 0.1, 0.1)
        elif active_alert:
            glColor3f(0.4, 0.05, 0.05)
        else:
            glColor3f(0.15, 0.8, 0.25)
        gluSphere(gluNewQuadric(), 4, 8, 8)
        glPopMatrix()
    glPopMatrix()


def draw_statue(e):
    scanner_glow(e["x"], e["y"], (1.0, 0.15, 0.15))
    glPushMatrix()
    glTranslatef(e["x"], e["y"], 40)
    if e["type"] == "watcher":
        glColor3f(0.55, 0.15, 0.65) if e["state"] != "FROZEN" else glColor3f(0.35, 0.35, 0.4)
    elif e["type"] == "uturn":
        glColor3f(0.6, 0.35, 0.1)
    else:
        glColor3f(0.5, 0.1, 0.55)
    gluCylinder(gluNewQuadric(), 28, 0.5, 80, 10, 4)
    glPopMatrix()


def draw_ghost(e):
    scanner_glow(e["x"], e["y"], (0.3, 1.0, 1.0))
    glPushMatrix()
    glTranslatef(e["x"], e["y"], e["z"] + 8 * math.sin(time.time() * 3))
    glColor3f(0.5, 0.95, 1.0)
    gluSphere(gluNewQuadric(), 26, 10, 10)
    glPopMatrix()


def draw_bullet_trails():
    glLineWidth(2)
    glColor3f(1.0, 0.9, 0.4)
    glBegin(GL_LINES)
    for b in BULLET_TRAILS:
        glVertex3f(b["x0"], b["y0"], b["z0"])
        glVertex3f(b["x1"], b["y1"], b["z1"])
    glEnd()


def draw_ghost_projectiles():
    glColor3f(0.4, 1.0, 1.0)
    for p in GHOST_PROJECTILES:
        glPushMatrix()
        glTranslatef(p["x"], p["y"], p["z"])
        gluSphere(gluNewQuadric(), 8, 8, 8)
        glPopMatrix()


def draw_player_model():
    glPushMatrix()
    glTranslatef(player["x"], player["y"], player["z"])
    glRotatef(player["angle"], 0, 0, 1)

    if camera_mode != "FIRST_PERSON":
        if player["shield_timer"] > 0:
            glColor3f(1.0, 1.0, 0.2)
        elif player["speed_timer"] > 0:
            glColor3f(0.2, 0.5, 1.0)
        elif player["damage_timer"] > 0:
            glColor3f(1.0, 0.25, 0.25)
        elif player["in_slip_zone"] and not player["sprinting"]:
            glColor3f(0.9, 0.2, 0.2)
        else:
            glColor3f(1.0, 1.0, 1.0)

        quad = gluNewQuadric()


        

        # torso
        glPushMatrix()
        glTranslatef(0, 0, 30)
        glScalef(22, 14, 34)
        glutSolidCube(1)
        glPopMatrix()

        # arms
        for side in (-1, 1):
            glPushMatrix()
            glTranslatef(0, side * 15, 53)
            glRotatef(90, 0, 1, 0)
            gluCylinder(quad, 5, 4, 24, 8, 2)
            glPopMatrix()

        # head
        glPushMatrix()
        glTranslatef(0, 0, 72)
        gluSphere(quad, 13, 10, 10)
        glPopMatrix()

    # Gun: fire
    glPushMatrix()
    if camera_mode == "FIRST_PERSON":
        glTranslatef(*GUN_LOCAL_OFFSET_FP)
    else:
        glTranslatef(*GUN_LOCAL_OFFSET_TP)

    # gun body - bright orange so it stands out against the dark museum environment
    glColor3f(1.0, 0.55, 0.05)
    glPushMatrix()
    glScalef(22, 7, 7)
    glutSolidCube(1)
    glPopMatrix()

    # gun barrel
    glColor3f(0.12, 0.12, 0.12)
    glPushMatrix()
    glTranslatef(15, 0, 0)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 2.5, 2.5, 14, 8, 2)
    glPopMatrix()

    glPopMatrix()
    glPopMatrix()


def draw_shapes():
    draw_floor()
    draw_room()
    for gate in GATES:
        draw_gate(gate)
    for a in ARTIFACTS:
        draw_artifact_obj(a)
    for g in GENERATORS:
        draw_generator_obj(g)
    for sw in SWITCHES:
        draw_switch_obj(sw)
    draw_spike_trap()
    draw_laser_trap()
    for pu in POWERUPS:
        draw_powerup_obj(pu)
    draw_security_console()
    for e in ENEMIES:
        if e["health"] <= 0:
            continue
        if e["type"] == "ghost":
            draw_ghost(e)
        else:
            draw_statue(e)
    draw_bullet_trails()
    draw_ghost_projectiles()
    draw_player_model()

# =====================================================================
# INPUT
# =====================================================================

def try_move(dx, dy):
    nx, ny = player["x"] + dx, player["y"] + dy
    nx = max(X0 + PLAYER_RADIUS, min(X1 - PLAYER_RADIUS, nx))
    ny = max(Y_MAIN0 + PLAYER_RADIUS, min(Y_END - PLAYER_RADIUS, ny))
    if not check_wall_collision(nx, player["y"]):
        player["x"] = nx
    if not check_wall_collision(player["x"], ny):
        player["y"] = ny


def detect_shift(key):
    
    return key.isalpha() and key.isupper()


def key_held(key):
    
    return (time.time() - key_last_seen.get(key, 0.0)) < KEY_HOLD_TIMEOUT


def keyboardListener(key, x, y):
    global game_over, game_won, sprint_last_seen
    shift_now = detect_shift(key)
    key = key.lower()

    if game_over or game_won:
        if key == b't':
            reset_game()
        return

    if key in (b'w', b's', b'a', b'd'):
        key_last_seen[key] = time.time()
        if shift_now:
            sprint_last_seen = time.time()
        
        if shift_now and not player["is_jumping"]:
            player["vz"] = JUMP_FORCE
            player["is_jumping"] = True
    if key == b' ':
        if not player["is_jumping"]:
            player["vz"] = JUMP_FORCE
            player["is_jumping"] = True
    if key == b'r':
        start_reload()
    if key == b'v':
        player["scanner_timer"] = SCANNER_DURATION
        add_message("Scanner activated")
    if key == b'c':
        cycle_camera()
    if key == b't':
        reset_game()
    if key.lower() == b'e':
        try_interact()


def cycle_camera():
    global camera_mode
    order = ["FIRST_PERSON", "THIRD_PERSON", "TOP_DOWN"]
    camera_mode = order[(order.index(camera_mode) + 1) % len(order)]
    add_message(f"Camera: {camera_mode}")


def start_reload():
    if player["reloading"] or player["ammo_reserve"] <= 0 or player["ammo_loaded"] == 6:
        return
    player["reloading"] = True
    player["reload_timer"] = 1.2
    add_message("Reloading...")


def try_interact():
   
    global power_restored, security_active, shutdown_active

    for g in GENERATORS:
        if not g["active"] and dist2(g["x"], g["y"], player["x"], player["y"]) < 55 ** 2:
            g["active"] = True
            add_message(f"GENERATOR {g['id']} ACTIVATED")
            if all(x["active"] for x in GENERATORS):
                power_restored = True
                security_active = True
                add_message("POWER RESTORED - SECURITY SYSTEM ACTIVATED!", 4)
                globals()["alarm_active"] = True

    for a in ARTIFACTS:
        if not a["collected"] and dist2(a["x"], a["y"], player["x"], player["y"]) < 50 ** 2:
             
            

            a["collected"] = True
            collected_now = sum(1 for x in ARTIFACTS if x["collected"])
            add_message(f"Collected: {a['name']}")
            add_message(f"Artifact collected. Artifacts: {collected_now}/{len(ARTIFACTS)}")

    for sw in SWITCHES:
        if not sw["used"] and dist2(sw["x"], sw["y"], player["x"], player["y"]) < 50 ** 2:
            sw["used"] = True
            apply_switch(sw)

    if (security_active and not security_disabled and not shutdown_active and
            dist2(SECURITY_CONSOLE["x"], SECURITY_CONSOLE["y"], player["x"], player["y"]) < 60 ** 2):
        shutdown_active = True
        globals()["shutdown_progress"] = 0.0
        add_message("DISABLING SECURITY... survive!", 3)
        for e in ENEMIES:
            if Y_G4 <= e["y"] <= Y_G5:
                e["state"] = "CHASE"


def apply_switch(sw):
    if sw["fn"] == "vault":
        add_message("Switch A: the vault door at the Ancient Gallery entrance unlocks")
    elif sw["fn"] == "laser_off":
        LASER["disabled"] = True
        add_message("Switch B: laser traps disabled")
    elif sw["fn"] == "spikes_off":
        SPIKES["disabled"] = True
        add_message("Switch C: spikes disabled")
    elif sw["fn"] == "alarm_pause":
        globals()["alarm_pause_timer"] = 8.0
        add_message("Switch D: alarm paused temporarily")


def specialKeyListener(key, x, y):
    global camera_orbit, camera_height_offset
    if key == GLUT_KEY_LEFT:
        camera_orbit -= 3
    if key == GLUT_KEY_RIGHT:
        camera_orbit += 3
    if key == GLUT_KEY_UP:
        camera_height_offset = min(300, camera_height_offset + 6)
    if key == GLUT_KEY_DOWN:
        camera_height_offset = max(-100, camera_height_offset - 6)


def mouseListener(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        shoot()
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        cycle_camera()


def gun_muzzle_world():
   
    local_x, local_y, local_z = GUN_LOCAL_OFFSET_FP if camera_mode == "FIRST_PERSON" else GUN_LOCAL_OFFSET_TP
    local_x += GUN_MUZZLE_FORWARD
    a = math.radians(player["angle"])
    wx = player["x"] + local_x * math.cos(a) - local_y * math.sin(a)
    wy = player["y"] + local_x * math.sin(a) + local_y * math.cos(a)
    wz = player["z"] + local_z
    return wx, wy, wz


# 

def raycast_wall_stop(x0, y0, tx, ty, max_dist):
    dx, dy = tx - x0, ty - y0
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return x0, y0
    dist = min(dist, max_dist)
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    steps = max(int(dist), 1)
    for i in range(1, steps + 1):
        px, py = x0 + ux * i, y0 + uy * i
        for (cx, cy, hw, hd, _h) in WALLS:
            if point_in_rect(px, py, cx, cy, hw, hd):
                return px, py
        # a still-closed gate blocks shots too
        for gate in GATES:
            if gate["open_progress"] < 0.9:
                gcx, gcy, ghw, ghd, _gh = gate_wall_box(gate)
                if point_in_rect(px, py, gcx, gcy, ghw, ghd):
                    return px, py
    return x0 + ux * dist, y0 + uy * dist


def shoot():
    
    if game_over or game_won:
        return
    if player["reloading"]:
        return
    if player["ammo_loaded"] <= 0:
        start_reload()
        return
    player["ammo_loaded"] -= 1

    best = None
    best_d = 500
    for e in ENEMIES:
        if e["health"] <= 0:
            continue
        d = math.hypot(e["x"] - player["x"], e["y"] - player["y"])
        if d > 500:
            continue
        ang_to = math.degrees(math.atan2(e["y"] - player["y"], e["x"] - player["x"]))
        diff = abs((ang_to - player["angle"] + 180) % 360 - 180)
        # an enemy behind a wall is not a valid target
        if diff < 35 and d < best_d and not line_of_sight_blocked(player["x"], player["y"], e["x"], e["y"]):
            best_d = d
            best = e

    mx, my, mz = gun_muzzle_world()   # bullets start at the gun's barrel tip

    if best:
        end_x, end_y = raycast_wall_stop(mx, my, best["x"], best["y"], best_d + 50)
        reached_enemy = abs(end_x - best["x"]) < 1.0 and abs(end_y - best["y"]) < 1.0
        if reached_enemy:
            dmg = 14 if player["damage_timer"] <= 0 else 28
            best["health"] -= dmg
            if best["health"] <= 0:
                add_message("Enemy destroyed")
        BULLET_TRAILS.append({"x0": mx, "y0": my, "z0": mz,
                               "x1": end_x, "y1": end_y, "z1": best["z"], "life": 0.12})
    else:
        a = math.radians(player["angle"])
        tx = mx + math.cos(a) * 400
        ty = my + math.sin(a) * 400
        
        end_x, end_y = raycast_wall_stop(mx, my, tx, ty, 400)
        BULLET_TRAILS.append({"x0": mx, "y0": my, "z0": mz,
                               "x1": end_x, "y1": end_y,
                               "z1": mz, "life": 0.12})

# =====================================================================
# CAMERA
# =====================================================================

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90, 1.25, 0.1, 2200)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    px, py, pz = player["x"], player["y"], player["z"]

    if camera_mode == "FIRST_PERSON":
        a = math.radians(player["angle"])
        eye_z = pz + 80        # above the humanoid model's head
        eye = (px, py, eye_z)
        look = (px + math.cos(a) * 100, py + math.sin(a) * 100, eye_z)
        gluLookAt(*eye, *look, 0, 0, 1)
    elif camera_mode == "TOP_DOWN":
        gluLookAt(px, py, 650 + camera_height_offset, px, py, 0, 0, 1, 0)
    else:
        a = math.radians(camera_orbit)
        dist = 260
        ex = px - math.cos(a) * dist
        ey = py - math.sin(a) * dist
        ez = pz + 160 + camera_height_offset * 0.3
        gluLookAt(ex, ey, ez, px, py, pz + 40, 0, 0, 1)

# =====================================================================
# UPDATE LOGIC
# =====================================================================

def update_gates(dt):
    for gate in GATES:
        cond = gate["condition"]
        unlock = False
        if cond == "switchA":
            unlock = SWITCHES[0]["used"]
        elif cond == "gen1":
            unlock = GENERATORS[0]["active"]
        elif cond == "gen2":
            unlock = GENERATORS[1]["active"]
        elif cond == "gen3":
            unlock = GENERATORS[2]["active"]
        elif cond == "security":
            unlock = security_disabled
        if unlock and gate["locked"]:
            gate["locked"] = False
            if not gate["slip_added"]:
                SLIP_ZONES.append((0, gate["y"] - 40, 35, 20))
                gate["slip_added"] = True
            add_message("A gate unlocks - the floor in front looks slippery...")
        if not gate["locked"] and gate["open_progress"] < 1.0:
            gate["open_progress"] = min(1.0, gate["open_progress"] + dt / 1.2)


def update_stamina_and_zones(dt):
    zone = in_slip_zone(player["x"], player["y"])
    player["in_slip_zone"] = zone
    if zone:
        if player["sprinting"] and player["stamina"] > 0:
            player["stamina"] -= ZONE_SPRINT_DRAIN_RATE * dt
        else:
            player["stamina"] -= ZONE_WALK_DRAIN_RATE * dt
            if random.random() < SLIP_CHANCE_PER_SEC * dt and player["shield_timer"] <= 0:
                player["health"] -= SLIP_DAMAGE
                player["slip_flash"] = 0.6
                add_message("You slipped on the floor!", 1.5)
    else:
        if player["sprinting"]:
            player["stamina"] -= SPRINT_DRAIN_RATE * dt
        else:
            player["stamina"] = min(player["max_stamina"], player["stamina"] + STAMINA_REGEN_RATE * dt)

    if player["stamina"] <= 0:
        player["stamina"] = 0
        player["sprinting"] = False
        if zone:
            player["health"] -= SLIP_DAMAGE * 1.5
            player["slip_flash"] = 0.6
            add_message("Exhausted - you fall on the slippery floor!", 1.5)

    if player["slip_flash"] > 0:
        player["slip_flash"] -= dt


def update_traps(dt):
    if dist2(PRESSURE_PLATE["x"], PRESSURE_PLATE["y"], player["x"], player["y"]) < 45 ** 2:
        if PRESSURE_PLATE["triggered_timer"] <= 0 and not SPIKES["disabled"]:
            PRESSURE_PLATE["triggered_timer"] = 2.0
            SPIKES["active"] = True
            add_message("Pressure plate triggered - spikes rising!")

    if PRESSURE_PLATE["triggered_timer"] > 0:
        PRESSURE_PLATE["triggered_timer"] -= dt
        if PRESSURE_PLATE["triggered_timer"] <= 0:
            SPIKES["active"] = False

    if SPIKES["active"] and not SPIKES["disabled"] and player["shield_timer"] <= 0:
        if circle_rect_collides(player["x"], player["y"], PLAYER_RADIUS,
                                 SPIKES["x"], SPIKES["y"], SPIKES["hw"], SPIKES["hd"]):
            player["health"] -= 30 * dt

    if not LASER["disabled"] and LASER["active"] and player["shield_timer"] <= 0:
        lx0, lx1, ly = LASER["x0"], LASER["x1"], LASER["y"]
        if min(lx0, lx1) - 15 <= player["x"] <= max(lx0, lx1) + 15 and abs(player["y"] - ly) < 15:
            player["health"] -= 25 * dt


def update_powerups(dt):
    for pu in POWERUPS:
        if pu["alive"]:
            if dist2(pu["x"], pu["y"], player["x"], player["y"]) < 40 ** 2:
                pu["alive"] = False
                pu["respawn"] = 20.0
                if pu["type"] == "shield":
                    player["shield_timer"] = 10.0
                    add_message("SHIELD ACTIVE")
                elif pu["type"] == "speed":
                    player["speed_timer"] = 10.0
                    add_message("SPEED BOOST ACTIVE")
                elif pu["type"] == "damage":
                    player["damage_timer"] = 10.0
                    add_message("DAMAGE BOOST ACTIVE")
        else:
            pu["respawn"] -= dt
            if pu["respawn"] <= 0:
                pu["alive"] = True

    for key in ("shield_timer", "speed_timer", "damage_timer"):
        if player[key] > 0:
            player[key] -= dt


def update_player(dt):
    
    moving = False
    dx = dy = 0.0
    if key_held(b'w'):
        dy += 1; moving = True
    if key_held(b's'):
        dy -= 1; moving = True
    if key_held(b'a'):
        dx -= 1; moving = True
    if key_held(b'd'):
        dx += 1; moving = True

    sprint_requested = (time.time() - sprint_last_seen) < KEY_HOLD_TIMEOUT
    can_sprint = sprint_requested and player["stamina"] > 0 and moving
    player["sprinting"] = can_sprint

    speed = MOVE_SPEED
    if can_sprint:
        speed *= SPRINT_MULT
    if player["speed_timer"] > 0:
        speed *= SPEED_POWERUP_MULT

    if moving:
        length = math.hypot(dx, dy)
        if length > 0:   
            dx, dy = dx / length, dy / length
            player["angle"] = math.degrees(math.atan2(dy, dx))
            try_move(dx * speed * dt, dy * speed * dt)

    over_hole = in_hole(player["x"], player["y"])
    ground = -9999 if over_hole else ground_height(player["x"], player["y"])

    if player["is_jumping"] or player["z"] > ground:
        player["vz"] -= GRAVITY * dt
        player["z"] += player["vz"] * dt
        if player["z"] <= ground and not over_hole:
            player["z"] = ground
            player["vz"] = 0
            player["is_jumping"] = False
        elif over_hole and player["z"] <= -400:
            player["health"] -= 25
            add_message("You fell into a hole!")
            player["x"], player["y"], player["z"] = 0, Y_MAIN0 + 40, 0
            player["vz"] = 0
            player["is_jumping"] = False
    else:
        player["z"] = ground

    update_stamina_and_zones(dt)
    update_traps(dt)
    update_powerups(dt)

    if player["reloading"]:
        player["reload_timer"] -= dt
        if player["reload_timer"] <= 0:
            player["reloading"] = False
            need = 6 - player["ammo_loaded"]
            take = min(need, player["ammo_reserve"])
            player["ammo_loaded"] += take
            player["ammo_reserve"] -= take
            add_message("Reload complete")

    if player["scanner_timer"] > 0:
        player["scanner_timer"] -= dt

    if player["y"] > EXIT_Y and security_disabled:
        globals()["game_won"] = True
        add_message("YOU ESCAPED THE MUSEUM!", 999)


def enemy_speed_mult():
    return 1.6 if alarm_active and alarm_pause_timer <= 0 else 1.0


def update_enemy(e, dt):
    
    if e["health"] <= 0:
        return
    if e.get("asleep_until_alarm") and not alarm_active:
        return

    y0, y1 = e["room_y"]
    dist_to_player = math.hypot(player["x"] - e["x"], player["y"] - e["y"])
    detect_range = 300 if alarm_active else 220
    speed = e["speed"] * enemy_speed_mult()

    if e["type"] == "hunter":
        if dist_to_player < detect_range:
            e["state"] = "CHASE"
        if e["state"] == "CHASE":
            ang = math.atan2(player["y"] - e["y"], player["x"] - e["x"])
            try_move_entity(e, math.cos(ang) * speed * dt, math.sin(ang) * speed * dt)
            e["y"] = max(y0, min(y1, e["y"]))
            if dist_to_player < 40 and player["shield_timer"] <= 0:
                player["health"] -= 18 * dt

    elif e["type"] == "uturn":
        if dist_to_player < detect_range:
            e["state"] = "CHASE"
        if e["state"] == "CHASE":
            # waypoint 1 2 3 4
            #line straight (player er majhe room ache kina)
            if not line_of_sight_blocked(e["x"], e["y"], player["x"], player["y"]):
                ang = math.atan2(player["y"] - e["y"], player["x"] - e["x"])
                try_move_entity(e, math.cos(ang) * speed * dt, math.sin(ang) * speed * dt)
            else:
                # player detection, chase kore
                wx, wy = e["waypoints"][e["wp_index"]]
                ang = math.atan2(wy - e["y"], wx - e["x"])
                try_move_entity(e, math.cos(ang) * speed * dt, math.sin(ang) * speed * dt)
                if math.hypot(wx - e["x"], wy - e["y"]) < 12:
                    e["wp_index"] = (e["wp_index"] + 1) % len(e["waypoints"])
            if dist_to_player < 40 and player["shield_timer"] <= 0:
                player["health"] -= 18 * dt

    elif e["type"] == "watcher":
        vec_to_statue = math.degrees(math.atan2(e["y"] - player["y"], e["x"] - player["x"]))
        diff = abs((vec_to_statue - player["angle"] + 180) % 360 - 180)
        looking_at_it = diff < 55 and dist_to_player < 400
        if looking_at_it:
            e["state"] = "FROZEN"
        else:
            e["state"] = "CHASE"
            ang = math.atan2(player["y"] - e["y"], player["x"] - e["x"])
            try_move_entity(e, math.cos(ang) * speed * dt, math.sin(ang) * speed * dt)
            e["y"] = max(y0, min(y1, e["y"]))
        if dist_to_player < 40 and player["shield_timer"] <= 0:
            player["health"] -= 18 * dt

    elif e["type"] == "ghost":
        pref = e["preferred_range"]
        if dist_to_player < detect_range or e["state"] != "IDLE":
            e["state"] = "ATTACK"
        if e["state"] == "ATTACK":
            ang = math.atan2(player["y"] - e["y"], player["x"] - e["x"])
            if dist_to_player > pref + 20:
                try_move_entity(e, math.cos(ang) * speed * dt, math.sin(ang) * speed * dt, radius=18)
            elif dist_to_player < pref - 20:
                try_move_entity(e, -math.cos(ang) * speed * dt, -math.sin(ang) * speed * dt, radius=18)
            e["y"] = max(y0, min(y1, e["y"]))
            e["attack_cd"] -= dt
            if e["attack_cd"] <= 0:
                e["attack_cd"] = 1.8
                spd = 140
                GHOST_PROJECTILES.append({
                    "x": e["x"], "y": e["y"], "z": e["z"],
                    "vx": math.cos(ang) * spd, "vy": math.sin(ang) * spd, "life": 3.0,
                })


def projectile_hits_wall(px, py):
    for (cx, cy, hw, hd, _h) in WALLS:
        if point_in_rect(px, py, cx, cy, hw, hd):
            return True
    for gate in GATES:
        if gate["open_progress"] < 0.9:
            cx, cy, hw, hd, _h = gate_wall_box(gate)
            if point_in_rect(px, py, cx, cy, hw, hd):
                return True
    return False


def update_projectiles(dt):
    for p in GHOST_PROJECTILES[:]:
        new_x = p["x"] + p["vx"] * dt
        new_y = p["y"] + p["vy"] * dt

        if projectile_hits_wall(new_x, new_y):
            GHOST_PROJECTILES.remove(p)   
            continue

        p["x"], p["y"] = new_x, new_y
        p["life"] -= dt
        if p["life"] <= 0:
            GHOST_PROJECTILES.remove(p)
            continue
        if dist2(p["x"], p["y"], player["x"], player["y"]) < 30 ** 2:
            if player["shield_timer"] <= 0:
                player["health"] -= 12
            GHOST_PROJECTILES.remove(p)

    for b in BULLET_TRAILS[:]:
        b["life"] -= dt
        if b["life"] <= 0:
            BULLET_TRAILS.remove(b)


def update_shutdown(dt):
    global shutdown_active, security_disabled
    if not shutdown_active:
        return
    globals()["shutdown_progress"] += (100.0 / 12.0) * dt
    if shutdown_progress >= 100:
        globals()["shutdown_progress"] = 100.0
        shutdown_active = False
        security_disabled = True
        globals()["alarm_active"] = False
        add_message("SECURITY SYSTEM DISABLED - FINAL EXIT UNLOCKED", 4)


def update_alarm(dt):
    global alarm_pause_timer
    if alarm_pause_timer > 0:
        alarm_pause_timer -= dt


def update_damage_feedback(dt):
    global prev_health, damage_flash_timer, damage_popup_timer, damage_popup_amount
    delta = prev_health - player["health"]
    if delta > 0.05:
        damage_flash_timer = 0.35
        damage_popup_timer = 1.0
        damage_popup_amount = int(round(delta))
        print(f"Player damaged. Damage: {damage_popup_amount}. "
              f"Current HP: {int(round(player['health']))}/{int(player['max_health'])}")
    prev_health = player["health"]
    if damage_flash_timer > 0:
        damage_flash_timer -= dt
    if damage_popup_timer > 0:
        damage_popup_timer -= dt


def update_hud_change_prints(dt):
    global prev_ammo_loaded, prev_ammo_reserve, prev_objective
    if player["ammo_loaded"] != prev_ammo_loaded or player["ammo_reserve"] != prev_ammo_reserve:
        print(f"Ammo updated: {player['ammo_loaded']}/{player['ammo_reserve']} (loaded/reserve)")
        prev_ammo_loaded = player["ammo_loaded"]
        prev_ammo_reserve = player["ammo_reserve"]

    obj = get_current_objective()
    if obj != prev_objective:
        print(f"Objective updated: {obj}")
        prev_objective = obj


def update_messages(dt):
    for m in messages:
        m[1] -= dt
    messages[:] = [m for m in messages if m[1] > 0]


def idle():
    global last_time, game_over
    now = time.time()
    dt = min(0.05, now - last_time)
    last_time = now

    if not game_over and not game_won:
        update_player(dt)
        update_gates(dt)
        for e in ENEMIES:
            update_enemy(e, dt)
        update_projectiles(dt)
        update_shutdown(dt)
        update_alarm(dt)
        update_damage_feedback(dt)
        update_hud_change_prints(dt)
        update_messages(dt)
        if player["health"] <= 0:
            game_over = True
            add_message("GAME OVER", 999)
    else:
        update_messages(dt)

    glutPostRedisplay()

# =====================================================================
# RESET
# =====================================================================

def reset_game():
    global game_over, game_won, power_restored, security_active
    global security_disabled, alarm_active, alarm_pause_timer
    global shutdown_active, shutdown_progress
    global prev_health, damage_flash_timer, damage_popup_timer, damage_popup_amount
    global prev_ammo_loaded, prev_ammo_reserve, prev_objective

    player.update({
        "x": 0.0, "y": Y_MAIN0 + 40, "z": 0.0, "vz": 0.0, "angle": 90.0,
        "is_jumping": False, "health": 100.0, "stamina": 100.0,
        "sprinting": False, "shield_timer": 0.0, "speed_timer": 0.0, "damage_timer": 0.0,
        "ammo_loaded": 6, "ammo_reserve": 24, "reloading": False, "reload_timer": 0.0,
        "in_slip_zone": False, "slip_flash": 0.0, "scanner_timer": 0.0,
    })
    for a in ARTIFACTS:
        a["collected"] = False
    for g in GENERATORS:
        g["active"] = False
    for sw in SWITCHES:
        sw["used"] = False
    PRESSURE_PLATE["triggered_timer"] = 0.0
    SPIKES["active"] = False
    SPIKES["disabled"] = False
    LASER["disabled"] = False
    for pu in POWERUPS:
        pu["alive"] = True
        pu["respawn"] = 0.0
    for gate in GATES:
        gate["locked"] = gate["condition"] is not None
        gate["open_progress"] = 0.0 if gate["condition"] is not None else 1.0
        gate["slip_added"] = gate["condition"] is None
    SLIP_ZONES[:] = list(BASE_SLIP_ZONES)

    starts = {1: (0, 500), 2: (0, 650), 3: (150, 850), 4: (100, 1100), 5: (-100, 1350), 6: (100, 1400)}
    for e in ENEMIES:
        e["x"], e["y"] = starts[e["id"]]
        e["state"] = "IDLE" if e["type"] != "hunter" or e["id"] != 1 else "PATROL"
        e["wp_index"] = 0
        e["health"] = e["max_health"]

    GHOST_PROJECTILES.clear()
    BULLET_TRAILS.clear()
    messages.clear()

    game_over = False
    game_won = False
    power_restored = False
    security_active = False
    security_disabled = False
    alarm_active = False
    alarm_pause_timer = 0.0
    shutdown_active = False
    shutdown_progress = 0.0
    prev_health = player["health"]
    damage_flash_timer = 0.0
    damage_popup_timer = 0.0
    damage_popup_amount = 0
    prev_ammo_loaded = player["ammo_loaded"]
    prev_ammo_reserve = player["ammo_reserve"]
    prev_objective = ""

    add_message("Museum reset - find Switch A to unlock the way into the museum!", 4)

# =====================================================================
# DISPLAY
# =====================================================================

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()
    draw_shapes()

    # HUD overlay
    glClear(GL_DEPTH_BUFFER_BIT)
    draw_hud()

    glutSwapBuffers()

# =====================================================================
# MAIN
# =====================================================================

def main():
    
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Night at the Museum - Haunted Escape")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    add_message("Find Switch A in the Main Hall to unlock the vault door", 5)
    add_message("SHIFT + W/A/S/D lets you jump across holes", 5)

    glutMainLoop()


if __name__ == "__main__":
    main()
