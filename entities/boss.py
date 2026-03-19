"""
Boss -- 4 variants with GIF animation, unique laser patterns and
progressive stat scaling.

Variants (random spawn with equal probability):
- Boss 0 (Titan):    Classic rotating cannons with 4 sub-patterns.
- Boss 1 (Fury):     Devastating rapid-fire bursts.
- Boss 2 (Fanblaze): Alternating fan-wave spreads.
- Boss 3 (Vortex):   Rotating spiral arms that accelerate.

Each successive defeat increases the next boss's stats.
"""

import math
import random
import pygame

from core.constants import (
    SCREEN_WIDTH, WHITE, RED, GREEN, YELLOW, ORANGE, CYAN, MAGENTA,
    NUM_BOSS_VARIANTS, BOSS_NAMES,
)
from core.assets import Assets
from entities.laser import Laser


class Boss:
    """Boss enemy with animated GIF, unique fire patterns and a health bar.

    Args:
        variant: Boss variant index (0--3).
    """

    def __init__(self, variant: int = 0) -> None:
        self.variant = variant % NUM_BOSS_VARIANTS
        self.width = 200
        self.height = 94
        self.x = float(SCREEN_WIDTH // 2 - self.width // 2)
        self.y = float(-self.height)

        self.target_y = 30
        self.entering = True
        self.alive = True

        # Stats (may be overridden by game.py scaling logic)
        self.max_hp = 60
        self.hp = self.max_hp

        # Horizontal movement
        self.h_speed = random.choice([-2.5, -2.0, -1.5, 1.5, 2.0, 2.5])
        self.h_dir_timer = 0
        self.h_dir_interval = random.randint(120, 300)

        # GIF animation
        self.frames = Assets.boss_variant_frames[self.variant]
        self.frame_idx = 0
        self.frame_timer = 0
        self.frame_delay = 6

        # Cannon positions (fractional offsets relative to width/height)
        self.cannon_offsets = [
            (0.12, 0.85),
            (0.38, 0.95),
            (0.62, 0.95),
            (0.88, 0.85),
        ]

        # Primary fire timer
        self.shoot_timer = 0
        self.shoot_interval = 40

        # Visual hit-flash
        self.hit_flash = 0
        self.hit_flash_max = 8

        # Spiral angle accumulator (for Vortex)
        self._spiral_angle = 0.0

        # Titan: cannon rotation counter
        self._titano_rotation = 0

        # Fury: burst counter and delay
        self._burst_count = 0
        self._burst_delay = 0

        # Fanblaze: alternating direction and wave counter
        self._fan_direction = 1
        self._fan_wave = 0

        # Vortex: spiral speed and acceleration
        self._spiral_speed = 0.4
        self._spiral_accel = 0.01

        # HP font (created once)
        self._hp_font = pygame.font.Font(None, 22)

        # Cached scaled sprite
        self._cached_scaled: pygame.Surface | None = None
        self._cached_w = 0
        self._cached_h = 0

    @staticmethod
    def random_variant() -> int:
        """Choose a random boss variant with equal probability."""
        return random.randint(0, NUM_BOSS_VARIANTS - 1)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update(self) -> list:
        """Update the boss: movement, animation and firing.

        Returns:
            List of newly spawned enemy ``Laser`` objects.
        """
        if not self.alive:
            return []

        # Entry phase: slide into view
        if self.entering:
            self.y += 1.5
            if self.y >= self.target_y:
                self.y = float(self.target_y)
                self.entering = False
            return []

        # Horizontal patrol movement
        self.x += self.h_speed
        self.h_dir_timer += 1
        if self.h_dir_timer >= self.h_dir_interval:
            self.h_speed = random.choice([-2.5, -2.0, -1.5, 1.5, 2.0, 2.5])
            self.h_dir_timer = 0
            self.h_dir_interval = random.randint(120, 300)

        # Bounce off screen edges
        if self.x <= 10:
            self.x = 10.0
            self.h_speed = abs(self.h_speed)
        elif self.x >= SCREEN_WIDTH - self.width - 10:
            self.x = float(SCREEN_WIDTH - self.width - 10)
            self.h_speed = -abs(self.h_speed)

        # Advance GIF animation
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            if self.frames:
                self.frame_idx = (self.frame_idx + 1) % len(self.frames)
                self._cached_scaled = None

        # Hit flash countdown
        if self.hit_flash > 0:
            self.hit_flash -= 1

        # Primary fire
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            return self._fire()

        # Secondary fire patterns (independent timer)
        return self._fire_secondary()

    # ------------------------------------------------------------------
    # FIRE PATTERNS
    # ------------------------------------------------------------------

    def _fire(self) -> list:
        """Execute the primary fire pattern for this variant."""
        if self.variant == 0:
            return self._fire_titan()
        elif self.variant == 1:
            return self._fire_fury()
        elif self.variant == 2:
            return self._fire_fanblaze()
        elif self.variant == 3:
            return self._fire_vortex()
        return self._fire_titan()

    def _fire_secondary(self) -> list:
        """Execute variant-specific secondary fire with its own timing."""
        lasers: list[Laser] = []

        # Fury: rapid burst between primary shots
        if self.variant == 1 and self._burst_delay > 0:
            self._burst_delay -= 1
            if self._burst_delay == 0 and self._burst_count > 0:
                self._burst_count -= 1
                self._burst_delay = 8
                cx, cy = self._cannon_pos(random.choice([0, 3]))
                lasers.append(Laser(cx, cy, 7, CYAN, is_enemy=True))
                if self._burst_count <= 0:
                    self._burst_delay = 0

        return lasers

    def _cannon_pos(self, idx: int) -> tuple[float, float]:
        """Compute the absolute position of cannon *idx*."""
        ox, oy = self.cannon_offsets[idx]
        return (
            self.x + int(self.width * ox) - 2,
            self.y + int(self.height * oy),
        )

    # -- TITAN (Boss 0): rotating cannon patterns --

    def _fire_titan(self) -> list:
        """Titan: cycles through 4 sub-patterns -- straight, converging,
        diverging and concentrated salvos.
        """
        lasers: list[Laser] = []
        self._titano_rotation = (self._titano_rotation + 1) % 4

        if self._titano_rotation == 0:
            # All 4 cannons fire straight down
            for i in range(4):
                cx, cy = self._cannon_pos(i)
                lasers.append(Laser(cx, cy, 5, ORANGE, is_enemy=True))

        elif self._titano_rotation == 1:
            # Outer cannons fire converging lasers
            center_x = self.x + self.width // 2
            for i in (0, 3):
                cx, cy = self._cannon_pos(i)
                dx = (center_x - cx) * 0.03
                lasers.append(Laser(cx, cy, 5, RED, is_enemy=True, vx=dx))

        elif self._titano_rotation == 2:
            # Inner cannons fire diverging lasers
            for i in (1, 2):
                cx, cy = self._cannon_pos(i)
                vx = -2.5 if i == 1 else 2.5
                lasers.append(Laser(cx, cy, 6, YELLOW, is_enemy=True, vx=vx))

        else:
            # Concentrated salvo aimed at a random X position
            target_x = random.randint(100, SCREEN_WIDTH - 100)
            for i in range(4):
                cx, cy = self._cannon_pos(i)
                dx = (target_x - cx) * 0.02
                lasers.append(Laser(cx, cy, 5.5, (255, 130, 50), is_enemy=True, vx=dx))

        return lasers

    # -- FURY (Boss 1): devastating bursts --

    def _fire_fury(self) -> list:
        """Fury: triple burst from each side cannon, then triggers a
        secondary auto-burst sequence.
        """
        lasers: list[Laser] = []
        for i in (0, 3):
            cx, cy = self._cannon_pos(i)
            for dy in (0, 10, 20):
                speed = 6 + dy * 0.1
                lasers.append(Laser(cx, cy + dy, speed, CYAN, is_enemy=True))

        # Activate secondary burst
        self._burst_count = 3
        self._burst_delay = 6
        return lasers

    # -- FANBLAZE (Boss 2): alternating fan waves --

    def _fire_fanblaze(self) -> list:
        """Fanblaze: 7-ray fan with oscillating spread and alternating
        direction.
        """
        lasers: list[Laser] = []
        center_x = self.x + self.width // 2
        center_y = self.y + self.height

        self._fan_wave += 1
        n_rays = 7
        spread = 30 + 30 * abs(math.sin(self._fan_wave * 0.3))

        base_angle = self._fan_direction * 10
        for i in range(n_rays):
            angle_deg = base_angle + (-spread + (2 * spread / (n_rays - 1)) * i)
            rad = math.radians(angle_deg)
            vx = math.sin(rad) * 4.5
            vy = math.cos(rad) * 5
            lasers.append(
                Laser(center_x - 2, center_y, vy, MAGENTA, is_enemy=True, vx=vx)
            )

        self._fan_direction *= -1
        return lasers

    # -- VORTEX (Boss 3): accelerating spiral arms --

    def _fire_vortex(self) -> list:
        """Vortex: 3 rotating spiral arms that gradually speed up."""
        lasers: list[Laser] = []
        center_x = self.x + self.width // 2
        center_y = self.y + self.height

        n_arms = 3
        for arm in range(n_arms):
            offset = (2 * math.pi / n_arms) * arm
            angle = self._spiral_angle + offset
            vx = math.sin(angle) * 3.5
            vy = math.cos(angle) * 4.0 + 1.5
            lasers.append(
                Laser(center_x - 2, center_y, vy, GREEN, is_enemy=True, vx=vx)
            )

        self._spiral_speed += self._spiral_accel
        if self._spiral_speed > 1.2:
            self._spiral_speed = 0.4  # reset
        self._spiral_angle += self._spiral_speed

        return lasers

    # ------------------------------------------------------------------
    # DAMAGE
    # ------------------------------------------------------------------

    def take_damage(self, amount: int = 1) -> bool:
        """Apply damage to the boss and trigger a visual hit-flash.

        Returns:
            True if the boss was killed.
        """
        self.hp -= amount
        self.hit_flash = self.hit_flash_max
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the boss with a pulse effect on hit."""
        if not self.alive or not self.frames:
            return

        frame = self.frames[self.frame_idx % len(self.frames)]

        if self.hit_flash > 0:
            ratio = self.hit_flash / self.hit_flash_max
            pulse = int(4 * ratio)
            w2 = self.width + pulse * 2
            h2 = self.height + pulse * 2
            scaled = pygame.transform.scale(frame, (w2, h2))
            surf.blit(scaled, (int(self.x) - pulse, int(self.y) - pulse))
            self._cached_scaled = None
        else:
            if (self._cached_scaled is None
                    or self._cached_w != self.width
                    or self._cached_h != self.height):
                self._cached_scaled = pygame.transform.scale(
                    frame, (self.width, self.height),
                )
                self._cached_w = self.width
                self._cached_h = self.height
            surf.blit(self._cached_scaled, (int(self.x), int(self.y)))

    def draw_health_bar(self, surf: pygame.Surface) -> None:
        """Draw the boss health bar at the top of the screen."""
        if not self.alive:
            return

        bw, bh = 400, 18
        bx = SCREEN_WIDTH // 2 - bw // 2
        by = 8

        # Background
        pygame.draw.rect(surf, (12, 12, 18), (bx - 1, by - 1, bw + 2, bh + 2))
        pygame.draw.rect(surf, (40, 40, 55), (bx, by, bw, bh))

        # Health fill
        pct = self.hp / self.max_hp
        if pct > 0.5:
            col = GREEN
        elif pct > 0.25:
            col = YELLOW
        else:
            col = RED

        fw = int(bw * pct)
        if fw > 0:
            pygame.draw.rect(surf, col, (bx, by, fw, bh))

        # Quarter-mark dividers
        for s in range(1, 4):
            sx = bx + bw * s // 4
            pygame.draw.line(surf, (12, 12, 18), (sx, by), (sx, by + bh), 1)

        # Boss name label
        vname = BOSS_NAMES[self.variant] if self.variant < len(BOSS_NAMES) else "BOSS"
        label = self._hp_font.render(f"{vname}  {self.hp}/{self.max_hp}", True, WHITE)
        surf.blit(label, (bx + bw // 2 - label.get_width() // 2, by + 1))

    def get_rect(self) -> pygame.Rect:
        """Return the boss collision hitbox."""
        return pygame.Rect(
            self.x + 15,
            self.y + 10,
            self.width - 30,
            self.height - 15,
        )
