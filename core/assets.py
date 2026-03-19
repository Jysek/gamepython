"""
Centralised asset loader.

All sprites (ships, enemies, lasers, asteroids, bosses, explosions,
power-ups) are loaded and pre-scaled once in ``Assets.load()``.

Animated GIFs (bosses, explosions, player ships, enemies) are
decomposed into individual frames via Pillow (PIL) and converted to
Pygame Surfaces for real-time rendering.

The ``resource_path()`` helper resolves paths correctly both when
running from source **and** from a PyInstaller frozen executable.
"""

import os
import sys
import pygame
from PIL import Image

from core.constants import (
    ENEMY_W, ENEMY_H, ASTEROID_SIZE, CARRIER_SIZE,
    POWERUP_ITEM_SIZE, EXPLOSION_SIZE, POWERUP_TYPES,
    NUM_PLAYER_SHIPS, NUM_BOSS_VARIANTS, PLAYER_W, PLAYER_H,
)

# ---------------------------------------------------------------------------
# Pre-scaled laser dimensions
# ---------------------------------------------------------------------------
_LASER_W = 20
_LASER_H = 40

# ---------------------------------------------------------------------------
# Asteroid trail spritestrip parameters (horizontal strip, 12 frames)
# ---------------------------------------------------------------------------
_TRAIL_FW = 32
_TRAIL_FH = 32
_TRAIL_N = 12

# ---------------------------------------------------------------------------
# Bounding boxes for player ships in navicelle.gif (3 rows x 4 cols).
# Computed from automatic pixel analysis (bg = RGB(29, 35, 40)).
# ---------------------------------------------------------------------------
_NAV_ROWS = [(30, 284), (316, 571), (603, 857)]
_NAV_COLS = [(25, 217), (246, 439), (466, 658), (687, 881)]
_NAV_BG = (29, 35, 40)

# ---------------------------------------------------------------------------
# Bounding boxes for 4 enemy ships in enemy_ships.gif.
# bg = RGB(255, 255, 255)
# ---------------------------------------------------------------------------
_ENEMY_COLS = [(38, 162), (202, 290), (341, 425), (479, 559)]
_ENEMY_ROW = (44, 160)
_ENEMY_BG = (255, 255, 255)


def resource_path(relative: str) -> str:
    """Return the absolute path to a bundled resource.

    Works both from source (normal Python) and from a PyInstaller
    one-file executable where resources are extracted into a temporary
    directory referenced by ``sys._MEIPASS``.

    Args:
        relative: Path relative to the project root (e.g.
                  ``'assets/ships/navicelle.gif'``).

    Returns:
        Absolute filesystem path.
    """
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # Running from source -- project root is one level above core/
        base = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
    return os.path.join(base, relative)


def _gif_frames(path: str) -> list[pygame.Surface]:
    """Decompose an animated GIF into individual Pygame Surfaces.

    Uses Pillow to read each frame, converts it to RGBA, then
    transforms it into a Pygame Surface with ``convert_alpha()``.

    Args:
        path: Absolute path to the GIF file.

    Returns:
        List of ``pygame.Surface`` (one per frame).
    """
    frames: list[pygame.Surface] = []
    gif = Image.open(path)
    for i in range(gif.n_frames):
        gif.seek(i)
        rgba = gif.convert("RGBA")
        data = rgba.tobytes()
        surf = pygame.image.fromstring(data, rgba.size, "RGBA").convert_alpha()
        frames.append(surf)
    return frames


def _gif_frames_remove_bg(
    path: str,
    bg: tuple[int, int, int],
    tolerance: int = 15,
) -> list[pygame.Surface]:
    """Like ``_gif_frames`` but removes a specific background colour."""
    frames: list[pygame.Surface] = []
    gif = Image.open(path)
    for i in range(gif.n_frames):
        gif.seek(i)
        rgba = gif.convert("RGBA")
        pixels = rgba.load()
        w, h = rgba.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if (abs(r - bg[0]) < tolerance
                        and abs(g - bg[1]) < tolerance
                        and abs(b - bg[2]) < tolerance):
                    pixels[x, y] = (0, 0, 0, 0)
        data = rgba.tobytes()
        surf = pygame.image.fromstring(data, rgba.size, "RGBA").convert_alpha()
        frames.append(surf)
    return frames


def _extract_ship_frames_from_gif(
    gif_path: str,
    row_bounds: list[tuple[int, int]],
    col_bounds: list[tuple[int, int]],
    bg: tuple[int, int, int],
    tolerance: int = 15,
) -> list[list[pygame.Surface]]:
    """Extract animated ship sprites from a grid-based GIF spritesheet.

    Each cell (row, col) in the grid contains one ship with multiple
    animation frames.  Background pixels are made transparent.

    Args:
        gif_path:   Path to the GIF spritesheet.
        row_bounds: List of (y_start, y_end) for each row.
        col_bounds: List of (x_start, x_end) for each column.
        bg:         RGB tuple of the background colour to remove.
        tolerance:  Colour matching tolerance.

    Returns:
        Nested list: ships[ship_index][frame_index] -> Surface.
    """
    gif = Image.open(gif_path)
    n_frames = gif.n_frames

    raw_frames: list[Image.Image] = []
    for i in range(n_frames):
        gif.seek(i)
        raw_frames.append(gif.convert("RGBA").copy())

    ships: list[list[pygame.Surface]] = []
    for ry1, ry2 in row_bounds:
        for cx1, cx2 in col_bounds:
            cell_frames: list[pygame.Surface] = []
            for frame in raw_frames:
                cell = frame.crop((cx1, ry1, cx2, ry2)).copy()
                pixels = cell.load()
                w, h = cell.size
                for y in range(h):
                    for x in range(w):
                        r, g, b, a = pixels[x, y]
                        if (abs(r - bg[0]) < tolerance
                                and abs(g - bg[1]) < tolerance
                                and abs(b - bg[2]) < tolerance):
                            pixels[x, y] = (0, 0, 0, 0)
                data = cell.tobytes()
                surf = pygame.image.fromstring(
                    data, cell.size, "RGBA",
                ).convert_alpha()
                cell_frames.append(surf)
            ships.append(cell_frames)
    return ships


def _extract_enemy_frames_from_gif(
    gif_path: str,
    col_bounds: list[tuple[int, int]],
    row_bound: tuple[int, int],
    bg: tuple[int, int, int],
    tolerance: int = 18,
) -> list[list[pygame.Surface]]:
    """Extract animated enemy sprites from a single-row GIF spritesheet.

    Args:
        gif_path:   Path to the GIF spritesheet.
        col_bounds: List of (x_start, x_end) for each enemy column.
        row_bound:  (y_start, y_end) for the single row.
        bg:         RGB tuple of background colour to remove.
        tolerance:  Colour matching tolerance.

    Returns:
        Nested list: enemies[type_index][frame_index] -> Surface.
    """
    gif = Image.open(gif_path)
    n_frames = gif.n_frames

    raw_frames: list[Image.Image] = []
    for i in range(n_frames):
        gif.seek(i)
        raw_frames.append(gif.convert("RGBA").copy())

    enemies: list[list[pygame.Surface]] = []
    ry1, ry2 = row_bound
    for cx1, cx2 in col_bounds:
        cell_frames: list[pygame.Surface] = []
        for frame in raw_frames:
            cell = frame.crop((cx1, ry1, cx2, ry2)).copy()
            pixels = cell.load()
            w, h = cell.size
            for y in range(h):
                for x in range(w):
                    r, g, b, a = pixels[x, y]
                    if (abs(r - bg[0]) < tolerance
                            and abs(g - bg[1]) < tolerance
                            and abs(b - bg[2]) < tolerance):
                        pixels[x, y] = (0, 0, 0, 0)
            data = cell.tobytes()
            surf = pygame.image.fromstring(
                data, cell.size, "RGBA",
            ).convert_alpha()
            cell_frames.append(surf)
        enemies.append(cell_frames)
    return enemies


class Assets:
    """Static container for all graphical game assets.

    Call ``Assets.load()`` once after ``pygame.display.set_mode()`` so
    that ``convert_alpha()`` can optimise the pixel format.
    """

    _loaded: bool = False

    # -- Player ships (5 types, animated) --
    player_ship_frames: list[list[pygame.Surface]] = []

    # -- Lasers (pre-scaled sprites per ship type) --
    laser_sprites: list[pygame.Surface] = []
    laser_left_angular: list[pygame.Surface] = []
    laser_right_angular: list[pygame.Surface] = []
    enemy_laser_sprite_scaled: pygame.Surface | None = None

    # -- Enemies (4 types, animated) --
    enemy_frames: dict[str, list[pygame.Surface]] = {}

    # -- Asteroid and trail --
    asteroid_sprite: pygame.Surface | None = None
    trail_frames: list[pygame.Surface] = []

    # -- Carrier and power-up --
    carrier_sprites: dict[str, pygame.Surface] = {}
    powerup_sprites: dict[str, pygame.Surface] = {}

    # -- Boss variants (animated frame lists) --
    boss_variant_frames: list[list[pygame.Surface]] = []

    # -- Explosions (frames from GIF) --
    explosion_frames: list[pygame.Surface] = []
    explosion_frames_raw: list[pygame.Surface] = []

    @classmethod
    def load(cls) -> None:
        """Load all graphical assets from disk.

        Assets are organised under ``assets/`` with sub-directories:
        - ``ships/``    -- player ship spritesheets
        - ``enemies/``  -- enemy spritesheets
        - ``bosses/``   -- boss GIF animations
        - ``lasers/``   -- laser sprites (66 PNG variants)
        - ``powerups/`` -- carrier and power-up sprites
        - ``sprites/``  -- asteroids and trails
        - ``effects/``  -- explosion GIF
        """
        if cls._loaded:
            return

        ships_dir = resource_path(os.path.join("assets", "ships"))
        enemies_dir = resource_path(os.path.join("assets", "enemies"))
        bosses_dir = resource_path(os.path.join("assets", "bosses"))
        lasers_dir = resource_path(os.path.join("assets", "lasers"))
        powerups_dir = resource_path(os.path.join("assets", "powerups"))
        sprites_dir = resource_path(os.path.join("assets", "sprites"))
        effects_dir = resource_path(os.path.join("assets", "effects"))

        def _load_img(
            directory: str,
            name: str,
            size: tuple[int, int] | None = None,
        ) -> pygame.Surface:
            """Load a single image, optionally rescaling it."""
            surf = pygame.image.load(
                os.path.join(directory, name),
            ).convert_alpha()
            return pygame.transform.scale(surf, size) if size else surf

        def _load_laser(name: str) -> pygame.Surface:
            """Load and scale a laser sprite to standard size."""
            return pygame.transform.scale(
                pygame.image.load(
                    os.path.join(lasers_dir, name),
                ).convert_alpha(),
                (_LASER_W, _LASER_H),
            )

        # ==============================================================
        # PLAYER SHIPS (5 animated ships from navicelle.gif)
        # ==============================================================
        all_ships = _extract_ship_frames_from_gif(
            os.path.join(ships_dir, "navicelle.gif"),
            _NAV_ROWS, _NAV_COLS, _NAV_BG, tolerance=15,
        )
        # Select 5 visually distinct ships from the 3x4 grid
        selected_indices = [1, 2, 5, 8, 11]
        cls.player_ship_frames = []
        for idx in selected_indices:
            if idx < len(all_ships):
                cls.player_ship_frames.append(all_ships[idx])
            else:
                cls.player_ship_frames.append(all_ships[-1])

        # ==============================================================
        # LASERS
        # ==============================================================
        base_lasers = [
            _load_laser("11.png"),
            _load_laser("16.png"),
            _load_laser("12.png"),
        ]
        base_left_angled = [
            _load_laser("11LeftAngular.png"),
            _load_laser("16LeftAngular.png"),
            _load_laser("12LeftAngular.png"),
        ]
        base_right_angled = [
            _load_laser("11RightAngular.png"),
            _load_laser("16RightAngular.png"),
            _load_laser("12RightAngular.png"),
        ]
        cls.laser_sprites = [
            base_lasers[i % 3] for i in range(NUM_PLAYER_SHIPS)
        ]
        cls.laser_left_angular = [
            base_left_angled[i % 3] for i in range(NUM_PLAYER_SHIPS)
        ]
        cls.laser_right_angular = [
            base_right_angled[i % 3] for i in range(NUM_PLAYER_SHIPS)
        ]
        cls.enemy_laser_sprite_scaled = _load_laser("14.png")

        # ==============================================================
        # ENEMIES (4 animated types from enemy_ships.gif)
        # ==============================================================
        enemy_type_names = ["scout", "fighter", "bomber", "elite"]
        raw_enemy = _extract_enemy_frames_from_gif(
            os.path.join(enemies_dir, "enemy_ships.gif"),
            _ENEMY_COLS, _ENEMY_ROW, _ENEMY_BG, tolerance=18,
        )
        cls.enemy_frames = {}
        for i, name in enumerate(enemy_type_names):
            cls.enemy_frames[name] = [
                pygame.transform.scale(f, (ENEMY_W, ENEMY_H))
                for f in raw_enemy[i]
            ]

        # ==============================================================
        # ASTEROID & TRAIL
        # ==============================================================
        cls.asteroid_sprite = _load_img(
            sprites_dir, "asteroid_1_rotondo.png",
            (ASTEROID_SIZE, ASTEROID_SIZE),
        )

        sheet = pygame.image.load(
            os.path.join(sprites_dir, "asteroid_trail.png"),
        ).convert_alpha()
        cls.trail_frames = []
        for i in range(_TRAIL_N):
            frame = sheet.subsurface(
                pygame.Rect(i * _TRAIL_FW, 0, _TRAIL_FW, _TRAIL_FH),
            ).copy()
            cls.trail_frames.append(frame)

        # ==============================================================
        # CARRIERS & POWER-UPS (use dedicated sprites for each type)
        # ==============================================================
        for pt in POWERUP_TYPES:
            carrier_file = f"carrier_{pt}.png"
            powerup_file = f"powerup_{pt}.png"
            cls.carrier_sprites[pt] = _load_img(
                powerups_dir, carrier_file, (CARRIER_SIZE, CARRIER_SIZE),
            )
            cls.powerup_sprites[pt] = _load_img(
                powerups_dir, powerup_file, (POWERUP_ITEM_SIZE, POWERUP_ITEM_SIZE),
            )

        # ==============================================================
        # BOSS VARIANTS (4 bosses, each an animated GIF)
        # ==============================================================
        boss_files = ["boss.gif", "boss_1.gif", "boss_2.gif", "boss_3.gif"]
        cls.boss_variant_frames = []
        for bf in boss_files:
            path = os.path.join(bosses_dir, bf)
            cls.boss_variant_frames.append(_gif_frames(path))

        # ==============================================================
        # EXPLOSIONS (animated GIF)
        # ==============================================================
        cls.explosion_frames_raw = _gif_frames(
            os.path.join(effects_dir, "explosionGif.gif"),
        )
        cls.explosion_frames = [
            pygame.transform.scale(f, (EXPLOSION_SIZE, EXPLOSION_SIZE))
            for f in cls.explosion_frames_raw
        ]

        cls._loaded = True
