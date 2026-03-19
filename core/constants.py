"""
Global game constants.

Contains all shared constants: screen dimensions, colours, sprite sizes,
power-up types, ship stats, enemy stats, and difficulty parameters.
"""

# ============================================================================
# SCREEN & RENDERING
# ============================================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# ============================================================================
# COLOURS (R, G, B)
# ============================================================================
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 50)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
DARK_GRAY = (30, 30, 40)
PANEL_BG = (20, 20, 35)
STAR_WHITE = (200, 200, 220)
GOLD = (255, 215, 0)

# ============================================================================
# SPRITE DIMENSIONS (pixels)
# ============================================================================
PLAYER_W = 60
PLAYER_H = 60
ENEMY_W = 60
ENEMY_H = 60
ASTEROID_SIZE = 60
CARRIER_SIZE = 55
POWERUP_ITEM_SIZE = 35
EXPLOSION_SIZE = 64

# Backward-compatible alias used internally by formations
ENEMY_SIZE = ENEMY_W

# ============================================================================
# PLAYER SHIPS -- 5 playable ships
# ============================================================================
NUM_PLAYER_SHIPS = 5

SHIP_NAMES = [
    "Viper",      # 0 -- Balanced all-rounder
    "Phoenix",    # 1 -- Tanky, slow fire rate
    "Striker",    # 2 -- Fast, fragile, piercing
    "Nova",       # 3 -- Double cannon, tactical (EMP)
    "Zenith",     # 4 -- Double cannon, destructive (Overdrive)
]

SHIP_DESCRIPTIONS = [
    "Agile and balanced",
    "Armoured and powerful",
    "Fast and lethal",
    "Double tactical cannon",
    "Supreme destroyer",
]

# Colour associated with each ship (used for lasers and HUD)
SHIP_COLORS = [
    GREEN,    # Viper
    MAGENTA,  # Phoenix
    ORANGE,   # Striker
    CYAN,     # Nova
    GOLD,     # Zenith
]

# Minimum score required to unlock each ship (0 = unlocked by default)
SHIP_UNLOCK_SCORES = [0, 200, 500, 1000, 2000]

# Double-cannon flag: True for the last two ships (Nova and Zenith)
SHIP_DOUBLE_CANNON = [False, False, False, True, True]

# ============================================================================
# PER-SHIP STATS (make each ship unique)
# ============================================================================
# Format: {speed, fire_rate, damage, special}
#   speed:     base speed multiplier (1.0 = normal)
#   fire_rate: shot cooldown multiplier (< 1.0 = faster firing)
#   damage:    damage per hit (1 = normal, 2 = double)
#   special:   unique ship ability
SHIP_STATS = [
    {"speed": 1.0, "fire_rate": 1.0, "damage": 1, "special": "none"},
    {"speed": 0.8, "fire_rate": 1.3, "damage": 2, "special": "regen"},
    {"speed": 1.4, "fire_rate": 0.6, "damage": 1, "special": "piercing"},
    {"speed": 1.1, "fire_rate": 0.85, "damage": 1, "special": "emp"},
    {"speed": 0.9, "fire_rate": 1.0, "damage": 2, "special": "overdrive"},
]

# ============================================================================
# POWER-UP TYPES
# ============================================================================
POWERUP_TYPES = ["vita", "scudo", "velocita", "arma", "bomba"]

POWERUP_COLORS = {
    "vita": GREEN,
    "scudo": CYAN,
    "velocita": YELLOW,
    "arma": ORANGE,
    "bomba": MAGENTA,
}

# ============================================================================
# BOSS VARIANTS
# ============================================================================
# 4 animated GIFs available: boss.gif, boss_1.gif, boss_2.gif, boss_3.gif
NUM_BOSS_VARIANTS = 4

BOSS_NAMES = [
    "Titan",       # Classic rotating cannons
    "Fury",        # Devastating bursts
    "Fanblaze",    # Alternating fan waves
    "Vortex",      # Rotating spiral arms
]

# ============================================================================
# ENEMY TYPE STATS
# ============================================================================
ENEMY_TYPE_STATS = {
    "scout":   {"hp": 1, "score": 1, "speed": 6, "color": "red"},
    "fighter": {"hp": 2, "score": 3, "speed": 5, "color": "orange"},
    "bomber":  {"hp": 4, "score": 5, "speed": 3, "color": "purple"},
    "elite":   {"hp": 3, "score": 8, "speed": 5, "color": "cyan"},
}

# ============================================================================
# PROGRESSIVE DIFFICULTY
# ============================================================================
DIFFICULTY_INTERVAL = 30       # seconds between difficulty increments
DIFFICULTY_SPEED_SCALE = 1.12  # enemy speed multiplier per level
DIFFICULTY_MAX_LEVEL = 10

# ============================================================================
# COMBO SYSTEM
# ============================================================================
COMBO_TIMEOUT_FRAMES = 150
COMBO_MULT_THRESHOLDS = [3, 6, 10, 15, 25]
COMBO_SCORE_BONUS = [0.5, 1.0, 1.5, 2.0, 3.0]

# ============================================================================
# SCREEN SHAKE
# ============================================================================
SHAKE_INTENSITY_LIGHT = 3
SHAKE_INTENSITY_MEDIUM = 6
SHAKE_INTENSITY_HEAVY = 10

# ============================================================================
# GRACE PERIOD
# ============================================================================
GRACE_PERIOD_FRAMES = 180

# ============================================================================
# SLOW MOTION (after boss kill)
# ============================================================================
SLOW_MO_DURATION = 90   # frames of slow motion after a boss kill
SLOW_MO_FACTOR = 0.4    # speed factor during slow-mo
