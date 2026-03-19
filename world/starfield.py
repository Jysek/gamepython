"""
StarField -- parallax star-field background.

Three depth layers with different star sizes and speeds create a
parallax scrolling effect that simulates flying through space.
"""

import random
import pygame

from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT


class StarField:
    """Parallax star field with three depth layers.

    Layer 0 (far):   small, slow stars.
    Layer 1 (mid):   medium stars at moderate speed.
    Layer 2 (near):  large, fast stars.
    """

    def __init__(self) -> None:
        """Generate stars for each depth layer."""
        self.layers: list[list[dict]] = []
        for speed, count, size in [(0.3, 50, 1), (0.7, 30, 2), (1.2, 15, 3)]:
            stars = []
            for _ in range(count):
                stars.append({
                    "x": random.randint(0, SCREEN_WIDTH),
                    "y": random.randint(0, SCREEN_HEIGHT),
                    "speed": speed,
                    "size": size,
                    "brightness": random.randint(100, 255),
                })
            self.layers.append(stars)

    def update(self) -> None:
        """Scroll stars downward; recycle to the top when off-screen."""
        for layer in self.layers:
            for star in layer:
                star["y"] += star["speed"]
                if star["y"] > SCREEN_HEIGHT:
                    star["y"] = 0
                    star["x"] = random.randint(0, SCREEN_WIDTH)
                    star["brightness"] = random.randint(100, 255)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all stars across all layers.

        Colour is a cool white-blue tint with variable brightness.
        """
        for layer in self.layers:
            for star in layer:
                b = star["brightness"]
                color = (b, b, min(255, b + 20))
                pygame.draw.circle(
                    surface, color,
                    (int(star["x"]), int(star["y"])), star["size"],
                )
