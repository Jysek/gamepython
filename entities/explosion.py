"""
Explosion -- animated explosion effect driven by a GIF spritesheet.

The explosion is centred on the given (x, y) point and plays through
all frames of ``explosionGif.gif``.  It deactivates automatically when
the animation ends.
"""

import pygame

from core.constants import EXPLOSION_SIZE
from core.assets import Assets


class Explosion:
    """Animated explosion effect.

    Args:
        x, y: Centre of the explosion (pixels).
        size: Rendered size in pixels (default ``EXPLOSION_SIZE``).
    """

    def __init__(self, x: float, y: float, size: int = EXPLOSION_SIZE) -> None:
        self.x = x
        self.y = y
        self.size = size
        self.active = True

        # Use pre-scaled frames when the size matches; otherwise scale on the fly
        if size == EXPLOSION_SIZE:
            self.frames = Assets.explosion_frames
        else:
            self.frames = [
                pygame.transform.scale(f, (size, size))
                for f in Assets.explosion_frames_raw
            ]

        self.frame_index = 0
        self.frame_delay = 2  # game ticks per GIF frame
        self.frame_timer = 0

    def update(self) -> None:
        """Advance the animation by one tick; deactivate at the last frame."""
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the current frame centred on (x, y).

        Args:
            surface: Destination surface.
        """
        if not self.active:
            return
        frame = self.frames[self.frame_index]
        surface.blit(
            frame,
            (int(self.x - self.size // 2), int(self.y - self.size // 2)),
        )
