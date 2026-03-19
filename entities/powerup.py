"""
PowerUpCarrier and FallingPowerUp -- power-up delivery system.

A carrier ship descends from the top, hovers for 5 seconds while moving
horizontally, and waits to be destroyed (3--5 HP).  When destroyed it
drops a falling power-up item for the player to collect.  If not
destroyed in time the carrier escapes with a hyper-speed dash.

Each power-up type has its own dedicated carrier and item sprite loaded
from ``assets/powerups/``.
"""

import math
import random
import pygame

from core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    CARRIER_SIZE, POWERUP_ITEM_SIZE, POWERUP_TYPES,
    WHITE, GREEN, CYAN, YELLOW, RED,
    POWERUP_COLORS,
)
from core.assets import Assets

# Carrier hit-shake parameters
_CARRIER_SHAKE_DURATION = 12
_CARRIER_SHAKE_AMPLITUDE = 3


class PowerUpCarrier:
    """Carrier ship that delivers a power-up when destroyed.

    Args:
        powerup_type: Type of power-up carried (random if ``None``).
    """

    STATE_DESCENDING = 0
    STATE_HOVERING = 1
    STATE_ESCAPING = 2

    def __init__(self, powerup_type: str | None = None) -> None:
        self.width = CARRIER_SIZE
        self.height = CARRIER_SIZE
        self.x: float = random.randint(20, SCREEN_WIDTH - self.width - 20)
        self.y: float = -self.height
        self.alive = True

        self.target_y = SCREEN_HEIGHT // 4
        self.state = PowerUpCarrier.STATE_DESCENDING
        self.descent_speed = 2.5

        # Power-up type and matching carrier sprite
        self.powerup_type = powerup_type or random.choice(POWERUP_TYPES)
        self.image = Assets.carrier_sprites[self.powerup_type]

        # Hit points
        self.max_hp = random.randint(3, 5)
        self.hp = self.max_hp

        # Horizontal movement
        self.h_speed = random.choice([-2.0, -1.5, -1.0, 1.0, 1.5, 2.0])
        self.h_direction_timer = 0
        self.h_change_interval = random.randint(60, 180)

        # Hover duration (5 seconds at 60 FPS)
        self.hover_timer = 5 * 60

        # Escape dash state
        self.escape_speed = 0.0
        self.escape_acceleration = 1.5
        self.hit_flash = 0
        self.trail_particles: list[dict] = []

        # Hit-shake state
        self._shake_timer = 0
        self._shake_offset_x = 0
        self._shake_offset_y = 0

        # HUD font (created once)
        self._hud_font = pygame.font.Font(None, 18)

    def update(self) -> None:
        """Advance the carrier based on its current state."""
        if not self.alive:
            return

        # Shake
        if self._shake_timer > 0:
            ratio = self._shake_timer / _CARRIER_SHAKE_DURATION
            amp = int(_CARRIER_SHAKE_AMPLITUDE * ratio)
            self._shake_offset_x = random.randint(-amp, amp)
            self._shake_offset_y = random.randint(-amp // 2, amp // 2)
            self._shake_timer -= 1
        else:
            self._shake_offset_x = 0
            self._shake_offset_y = 0

        if self.hit_flash > 0:
            self.hit_flash -= 1

        if self.state == self.STATE_DESCENDING:
            self._update_descending()
        elif self.state == self.STATE_HOVERING:
            self._update_hovering()
        elif self.state == self.STATE_ESCAPING:
            self._update_escaping()

    def _update_descending(self) -> None:
        """Descend from above to the target hover position."""
        self.y += self.descent_speed
        if self.y >= self.target_y:
            self.y = self.target_y
            self.state = self.STATE_HOVERING

    def _update_hovering(self) -> None:
        """Move horizontally and count down the hover timer."""
        self.x += self.h_speed
        self.h_direction_timer += 1
        if self.h_direction_timer >= self.h_change_interval:
            self.h_speed = random.choice([-2.0, -1.5, -1.0, 1.0, 1.5, 2.0])
            self.h_direction_timer = 0
            self.h_change_interval = random.randint(60, 180)

        # Bounce off edges
        if self.x < 10:
            self.x = 10
            self.h_speed = abs(self.h_speed)
        elif self.x > SCREEN_WIDTH - self.width - 10:
            self.x = SCREEN_WIDTH - self.width - 10
            self.h_speed = -abs(self.h_speed)

        self.hover_timer -= 1
        if self.hover_timer <= 0:
            self.state = self.STATE_ESCAPING
            self.escape_speed = 3.0

    def _update_escaping(self) -> None:
        """Accelerate downward in a hyper-speed escape dash."""
        self.escape_speed += self.escape_acceleration
        self.y += self.escape_speed

        if random.random() < 0.6:
            self.trail_particles.append({
                "x": self.x + self.width // 2 + random.randint(-10, 10),
                "y": self.y,
                "alpha": 200,
                "size": random.randint(2, 5),
            })

        for p in self.trail_particles:
            p["alpha"] -= 12
            p["size"] = max(0, p["size"] - 0.1)
        self.trail_particles = [
            p for p in self.trail_particles if p["alpha"] > 0
        ]

        if self.y > SCREEN_HEIGHT + 50:
            self.alive = False

    def take_damage(self, amount: int = 1) -> bool:
        """Apply damage to the carrier and trigger a shake.

        The mini-explosion is spawned by the caller (game.py) because it
        needs access to the global explosions list.

        Returns:
            True if the carrier was destroyed.
        """
        self.hp -= amount
        self._shake_timer = _CARRIER_SHAKE_DURATION

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the carrier with all visual effects."""
        if not self.alive:
            return

        # Escape trail
        if self.state == self.STATE_ESCAPING:
            self._draw_trail(surface)

        draw_img = self.image.copy()

        # Stretch during escape
        if self.state == self.STATE_ESCAPING:
            stretch_h = min(
                self.height + int(self.escape_speed * 2),
                self.height * 3,
            )
            draw_img = pygame.transform.scale(draw_img, (self.width, stretch_h))

        draw_x = int(self.x + self._shake_offset_x)
        draw_y = int(self.y + self._shake_offset_y)
        surface.blit(draw_img, (draw_x, draw_y))

        # HUD elements (not shown during escape)
        if self.state != self.STATE_ESCAPING:
            self._draw_carrier_hud(surface)

    def _draw_trail(self, surface: pygame.Surface) -> None:
        """Draw escape-trail particles."""
        for p in self.trail_particles:
            size = int(p["size"])
            if size <= 0:
                continue
            trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                trail_surf, (100, 180, 255, int(p["alpha"])),
                (size, size), size,
            )
            surface.blit(trail_surf, (int(p["x"] - size), int(p["y"] - size)))

    def _draw_carrier_hud(self, surface: pygame.Surface) -> None:
        """Draw the type label, HP bar and countdown bar."""
        color = POWERUP_COLORS.get(self.powerup_type, WHITE)

        label = self._hud_font.render(self.powerup_type.upper(), True, color)
        label_x = self.x + self.width // 2 - label.get_width() // 2
        surface.blit(label, (int(label_x), int(self.y - 14)))

        # HP bar
        bar_w = self.width
        bar_y = self.y + self.height + 2
        hp_pct = self.hp / self.max_hp
        pygame.draw.rect(surface, (60, 60, 60), (int(self.x), int(bar_y), bar_w, 4))
        pygame.draw.rect(surface, color, (int(self.x), int(bar_y), int(bar_w * hp_pct), 4))

        # Hover countdown bar
        if self.state == self.STATE_HOVERING:
            timer_bar_y = self.y + self.height + 8
            timer_pct = self.hover_timer / (5 * 60)
            if timer_pct > 0.5:
                timer_color = GREEN
            elif timer_pct > 0.25:
                timer_color = YELLOW
            else:
                timer_color = RED
            pygame.draw.rect(
                surface, (40, 40, 40),
                (int(self.x), int(timer_bar_y), bar_w, 3),
            )
            pygame.draw.rect(
                surface, timer_color,
                (int(self.x), int(timer_bar_y), int(bar_w * timer_pct), 3),
            )

    def get_rect(self) -> pygame.Rect:
        """Return the carrier collision hitbox."""
        shrink = 5
        return pygame.Rect(
            self.x + shrink,
            self.y + shrink,
            self.width - shrink * 2,
            self.height - shrink * 2,
        )


class FallingPowerUp:
    """Power-up item that falls after a carrier is destroyed.

    Args:
        x, y:         Initial position (centre of destroyed carrier).
        powerup_type: Type of power-up.
    """

    def __init__(self, x: float, y: float, powerup_type: str) -> None:
        self.width = POWERUP_ITEM_SIZE
        self.height = POWERUP_ITEM_SIZE
        self.x = x
        self.y = y
        self.powerup_type = powerup_type
        self.image = Assets.powerup_sprites[self.powerup_type]
        self.active = True
        self.fall_speed = 2.5
        self.pulse_timer = 0.0

    def update(self) -> None:
        """Move the power-up downward; deactivate when off-screen."""
        if not self.active:
            return
        self.y += self.fall_speed
        self.pulse_timer += 0.1
        if self.y > SCREEN_HEIGHT + 20:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the power-up with a pulsing glow effect."""
        if not self.active:
            return

        glow_alpha = int(abs(math.sin(self.pulse_timer)) * 80) + 40
        glow_color = POWERUP_COLORS.get(self.powerup_type, WHITE)
        glow_size = self.width + 10
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf, (*glow_color, glow_alpha),
            (glow_size // 2, glow_size // 2), glow_size // 2,
        )
        surface.blit(glow_surf, (int(self.x - 5), int(self.y - 5)))
        surface.blit(self.image, (int(self.x), int(self.y)))

    def get_rect(self) -> pygame.Rect:
        """Return the power-up collision hitbox."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
