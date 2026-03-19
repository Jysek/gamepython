"""
Laser and AngledLaser -- projectiles used by players and enemies.

Lasers can travel upward (player) or downward (enemy).  Sprites are
pre-scaled in ``Assets.load()`` to avoid per-frame scaling overhead.

Boss lasers support a horizontal velocity component (``vx``) for
diagonal / spiral patterns.
"""

import math
import pygame

from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, CYAN
from core.assets import Assets


class Laser:
    """Straight-line projectile (player or enemy).

    Supports an optional horizontal velocity for diagonal patterns.

    Args:
        x, y:     Initial position (top-left corner).
        speed:    Vertical speed (negative = up, positive = down).
        color:    Fallback colour if no sprite is available.
        is_enemy: True if this laser belongs to an enemy or boss.
        sprite:   Pre-loaded Pygame Surface (optional).
        vx:       Horizontal velocity (0 = straight). Used by bosses.
    """

    WIDTH = 20
    HEIGHT = 40

    def __init__(
        self,
        x: float,
        y: float,
        speed: float,
        color: tuple = CYAN,
        is_enemy: bool = False,
        sprite: pygame.Surface | None = None,
        vx: float = 0.0,
    ) -> None:
        self.x = x
        self.y = y
        self.speed = speed
        self.vx = vx
        self.color = color
        self.is_enemy = is_enemy
        self.active = True

        if sprite:
            self.image = sprite
        elif is_enemy:
            self.image = Assets.enemy_laser_sprite_scaled
        else:
            self.image = None

    def update(self) -> None:
        """Move the laser and deactivate it when off-screen."""
        self.y += self.speed
        self.x += self.vx
        margin = 50
        if self.y < -margin or self.y > SCREEN_HEIGHT + margin:
            self.active = False
        if self.x < -margin or self.x > SCREEN_WIDTH + margin:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        """Render the laser sprite (or a coloured rectangle as fallback)."""
        if self.image:
            surface.blit(self.image, (int(self.x), int(self.y)))
        else:
            pygame.draw.rect(
                surface, self.color,
                (int(self.x), int(self.y), self.WIDTH, self.HEIGHT),
            )

    def get_rect(self) -> pygame.Rect:
        """Return the collision hitbox (slightly narrower than sprite)."""
        shrink_x = 4
        return pygame.Rect(
            self.x + shrink_x,
            self.y,
            self.WIDTH - shrink_x * 2,
            self.HEIGHT,
        )


class AngledLaser(Laser):
    """Diagonal laser fired by the weapon power-up (triple shot).

    Travels along a trajectory determined by the given angle relative
    to the vertical axis.

    Args:
        x, y:       Initial position.
        base_speed: Base movement speed.
        angle_deg:  Angle in degrees from vertical.
        color:      Fallback colour.
        sprite:     Pre-loaded Pygame Surface (optional).
    """

    def __init__(
        self,
        x: float,
        y: float,
        base_speed: float,
        angle_deg: float,
        color: tuple = CYAN,
        sprite: pygame.Surface | None = None,
    ) -> None:
        super().__init__(x, y, base_speed, color, is_enemy=False, sprite=sprite)
        rad = math.radians(angle_deg)
        self.vx = -base_speed * math.sin(rad)
        self.vy = base_speed * math.cos(rad)
        self.angle_deg = angle_deg

    def update(self) -> None:
        """Move the laser along its angled trajectory."""
        self.x += self.vx
        self.y += self.vy
        margin = 50
        if self.y < -margin or self.y > SCREEN_HEIGHT + margin:
            self.active = False
        if self.x < -margin or self.x > SCREEN_WIDTH + margin:
            self.active = False
