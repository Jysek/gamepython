"""
Enemy -- animated sprite with hit-shake, HP bar, and type-based laser patterns.

Four enemy types extracted from ``enemy_ships.gif``:
- scout:   fast single laser, 1 HP, 1 point
- fighter: double parallel lasers, 2 HP, 3 points
- bomber:  slow triple parallel lasers, 4 HP, 5 points
- elite:   rapid 3-burst lasers, 3 HP, 8 points
"""

import random
import pygame

from core.constants import ENEMY_W, ENEMY_H, RED, ORANGE, YELLOW, CYAN, ENEMY_TYPE_STATS
from core.assets import Assets
from entities.formations import Slot

# ---------------------------------------------------------------------------
# Hit-shake parameters (frame-based)
# ---------------------------------------------------------------------------
_SHAKE_DURATION = 8
_SHAKE_AMPLITUDE = 3

# ---------------------------------------------------------------------------
# Laser colour per enemy type
# ---------------------------------------------------------------------------
_LASER_COLOR: dict[str, tuple] = {
    "scout": RED,
    "fighter": ORANGE,
    "bomber": (180, 0, 220),
    "elite": CYAN,
}

# Laser speed per type (pixels / frame)
_LASER_SPEED: dict[str, int] = {
    "scout": 6,
    "fighter": 5,
    "bomber": 3,
    "elite": 5,
}

# Shooting interval range (min, max) in frames
_SHOOT_INTERVAL: dict[str, tuple[int, int]] = {
    "scout": (70, 160),
    "fighter": (100, 200),
    "bomber": (160, 320),
    "elite": (80, 180),
}


class Enemy:
    """A single alien enemy with type, HP, animated sprite and fire pattern.

    Args:
        x, y:       Initial position.
        enemy_type: Enemy type key (scout / fighter / bomber / elite).
        hp:         Starting hit points.
    """

    def __init__(
        self,
        x: float,
        y: float,
        enemy_type: str = "scout",
        hp: int = 1,
    ) -> None:
        self.width = ENEMY_W
        self.height = ENEMY_H
        self.x = x
        self.y = y
        self.alive = True

        self.enemy_type = enemy_type
        self.hp = hp
        self.max_hp = hp

        self.h_speed = 0.0

        # Individual shoot timer
        lo, hi = _SHOOT_INTERVAL.get(enemy_type, (100, 200))
        self.shoot_timer = random.randint(0, hi)
        self.shoot_interval = random.randint(lo, hi)

        # Logical slot within the formation grid
        self.slot: Slot = Slot(0, 0)

        # Hit-shake state
        self._shake_timer = 0

        # GIF animation state
        self._frame_idx = 0
        self._frame_timer = 0
        self._frame_delay = 8

    # ------------------------------------------------------------------
    # DAMAGE
    # ------------------------------------------------------------------

    def take_damage(self, amount: int = 1) -> bool:
        """Apply damage and trigger a hit-shake.

        Returns:
            True if the enemy was killed.
        """
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True

        # Still alive: shake
        self._shake_timer = _SHAKE_DURATION
        return False

    # ------------------------------------------------------------------
    # ANIMATED SPRITE
    # ------------------------------------------------------------------

    def _get_frames(self) -> list[pygame.Surface]:
        """Return the animation frames for this enemy type."""
        frames = Assets.enemy_frames.get(self.enemy_type)
        if frames:
            return frames
        return Assets.enemy_frames.get("scout", [])

    # ------------------------------------------------------------------
    # LASER CONSTRUCTION
    # ------------------------------------------------------------------

    def build_lasers(self) -> list:
        """Build lasers according to this enemy type's fire pattern.

        Returns:
            List of ``Laser`` objects to be added to the game.
        """
        from entities.laser import Laser

        cx = self.x + self.width // 2
        by = self.y + self.height
        spd = _LASER_SPEED.get(self.enemy_type, 5)
        col = _LASER_COLOR.get(self.enemy_type, RED)
        lasers: list[Laser] = []

        if self.enemy_type == "scout":
            lasers.append(Laser(cx - 2, by, spd, col, is_enemy=True))

        elif self.enemy_type == "fighter":
            lasers.append(Laser(cx - 10, by, spd, col, is_enemy=True))
            lasers.append(Laser(cx + 8, by, spd, col, is_enemy=True))

        elif self.enemy_type == "bomber":
            for offset in (-8, -2, 4):
                lasers.append(Laser(cx + offset, by, spd, col, is_enemy=True))

        elif self.enemy_type == "elite":
            for dy in (0, 6, 12):
                lasers.append(Laser(cx - 2, by + dy, spd, col, is_enemy=True))

        else:
            lasers.append(Laser(cx - 2, by, spd, col, is_enemy=True))

        return lasers

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the animated enemy sprite with optional hit-shake."""
        if not self.alive:
            return

        # Advance animation
        self._frame_timer += 1
        if self._frame_timer >= self._frame_delay:
            self._frame_timer = 0
            frames = self._get_frames()
            if frames:
                self._frame_idx = (self._frame_idx + 1) % len(frames)

        # Compute shake offset
        offset_x = 0
        if self._shake_timer > 0:
            ratio = self._shake_timer / _SHAKE_DURATION
            offset_x = int(_SHAKE_AMPLITUDE * ratio) * (
                1 if self._shake_timer % 2 == 0 else -1
            )
            self._shake_timer -= 1

        frames = self._get_frames()
        if frames:
            frame = frames[self._frame_idx % len(frames)]
            surf.blit(frame, (int(self.x + offset_x), int(self.y)))
        else:
            pygame.draw.rect(
                surf, RED,
                (int(self.x + offset_x), int(self.y), self.width, self.height),
            )

        # HP bar for multi-HP enemies
        if self.max_hp > 1 and self.hp > 0:
            self._draw_hp_bar(surf)

    def _draw_hp_bar(self, surf: pygame.Surface) -> None:
        """Draw a small HP bar above the enemy."""
        bar_w = self.width - 10
        bar_h = 3
        bar_x = self.x + 5
        bar_y = self.y - 5

        pct = self.hp / self.max_hp
        pygame.draw.rect(surf, (40, 40, 40), (int(bar_x), int(bar_y), bar_w, bar_h))

        if pct > 0.5:
            col = (50, 255, 50)
        elif pct > 0.25:
            col = (255, 255, 50)
        else:
            col = (255, 50, 50)
        pygame.draw.rect(surf, col, (int(bar_x), int(bar_y), int(bar_w * pct), bar_h))

    # ------------------------------------------------------------------
    # HITBOX
    # ------------------------------------------------------------------

    def get_rect(self) -> pygame.Rect:
        """Return the collision hitbox (slightly shrunk)."""
        sx, sy = 6, 4
        return pygame.Rect(
            self.x + sx,
            self.y + sy,
            self.width - sx * 2,
            self.height - sy * 2,
        )
