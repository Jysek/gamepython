"""
Boss -- 4 variants with GIF animation, unique laser patterns and
progressive stat scaling.

Each boss has a single, clearly identifiable attack pattern that is
challenging but always possible to dodge:

- Boss 0 (Titan):    Alternating dual-cannon volleys -- straight down
                      from outer cannons, then converging from inner
                      cannons.  Leaves clear lateral safe zones.
- Boss 1 (Fury):     Staggered burst volleys -- fires 3-shot bursts
                      alternating left/right side with a pause between.
- Boss 2 (Fanblaze): Slow sweeping pendulum -- 3 lasers sweep smoothly
                      from one side to the other, then reverse.
                      Dodge by moving *with* the sweep direction.
- Boss 3 (Vortex):   Double helix -- two opposite spiral arms rotate
                      at a constant moderate speed.  Dodge by orbiting
                      in the same direction as the rotation.

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
    """Boss enemy with animated GIF, unique fire pattern and a health bar.

    Args:
        variant: Boss variant index (0--3).
    """

    def __init__(self, variant: int = 0) -> None:
        self.variant = variant % NUM_BOSS_VARIANTS
        self.width = 200
        self.height = 94
        self.x = float(SCREEN_WIDTH // 2 - self.width // 2)
        self.y = float(-self.height)

        self.target_y = 30.0
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

        # --- Pattern-specific state ---

        # Titan: alternating volley phase (0 = outer straight, 1 = inner converge)
        self._titan_phase = 0

        # Fury: side toggle and burst state
        self._fury_side = 0          # 0 = left, 1 = right
        self._fury_burst_left = 0    # remaining shots in current burst
        self._fury_burst_delay = 0   # frames between burst shots

        # Fanblaze: pendulum sweep angle and direction
        self._fan_angle = -30.0      # current sweep angle (degrees)
        self._fan_dir = 1            # +1 = sweeping right, -1 = sweeping left
        self._fan_sweep_speed = 1.2  # degrees per fire tick

        # Vortex: rotation angle for the double helix
        self._helix_angle = 0.0
        self._helix_speed = 0.08     # radians per frame

        # HP font (cached)
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
                self.y = self.target_y
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

        # Update Vortex helix rotation every frame (independent of fire)
        if self.variant == 3:
            self._helix_angle += self._helix_speed

        # Primary fire
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            return self._fire()

        # Fury burst continuation (fires between primary ticks)
        if self.variant == 1:
            return self._fury_burst_tick()

        return []

    # ------------------------------------------------------------------
    # FIRE PATTERNS  (redesigned: simple, unique, dodgeable)
    # ------------------------------------------------------------------

    def _fire(self) -> list:
        """Dispatch to the variant-specific fire pattern."""
        if self.variant == 0:
            return self._fire_titan()
        elif self.variant == 1:
            return self._fire_fury()
        elif self.variant == 2:
            return self._fire_fanblaze()
        elif self.variant == 3:
            return self._fire_vortex()
        return self._fire_titan()

    def _cannon_pos(self, idx: int) -> tuple[float, float]:
        """Compute the absolute position of cannon *idx*."""
        ox, oy = self.cannon_offsets[idx]
        return (
            self.x + int(self.width * ox) - 2,
            self.y + int(self.height * oy),
        )

    # -- TITAN (Boss 0): alternating dual-cannon volleys ----------------

    def _fire_titan(self) -> list:
        """Titan: alternates between two simple volley types.

        Phase 0 -- outer cannons (0, 3) fire straight down.
        Phase 1 -- inner cannons (1, 2) fire slightly converging
                   towards centre.

        The alternation creates a predictable rhythm the player can
        learn: dodge the outer shots, then dodge the inner ones.
        """
        lasers: list[Laser] = []
        if self._titan_phase == 0:
            # Outer cannons fire straight down
            for i in (0, 3):
                cx, cy = self._cannon_pos(i)
                lasers.append(Laser(cx, cy, 5.0, ORANGE, is_enemy=True))
        else:
            # Inner cannons fire converging towards screen centre
            center_x = self.x + self.width / 2
            for i in (1, 2):
                cx, cy = self._cannon_pos(i)
                dx = (center_x - cx) * 0.025
                lasers.append(Laser(cx, cy, 5.5, RED, is_enemy=True, vx=dx))

        self._titan_phase = 1 - self._titan_phase
        return lasers

    # -- FURY (Boss 1): staggered burst volleys -------------------------

    def _fire_fury(self) -> list:
        """Fury: fires a 3-shot burst from one side, then switches.

        Each burst fires 3 quick shots from either the left (cannon 0)
        or right (cannon 3) side.  After a burst completes the side
        toggles.  The spacing between individual burst shots is 6
        frames, giving the player time to weave between them.
        """
        # Start a new burst
        self._fury_burst_left = 3
        self._fury_burst_delay = 0
        return self._fury_emit_one()

    def _fury_burst_tick(self) -> list:
        """Continue an in-progress Fury burst (called every frame)."""
        if self._fury_burst_left <= 0:
            return []
        self._fury_burst_delay -= 1
        if self._fury_burst_delay <= 0:
            return self._fury_emit_one()
        return []

    def _fury_emit_one(self) -> list:
        """Emit a single laser from the active Fury side cannon."""
        if self._fury_burst_left <= 0:
            return []
        cannon_idx = 0 if self._fury_side == 0 else 3
        cx, cy = self._cannon_pos(cannon_idx)
        # Slight random spread to add variety but keep it simple
        vx = random.uniform(-0.4, 0.4)
        laser = Laser(cx, cy, 6.0, CYAN, is_enemy=True, vx=vx)
        self._fury_burst_left -= 1
        self._fury_burst_delay = 6
        if self._fury_burst_left <= 0:
            # Burst finished, toggle side for next burst
            self._fury_side = 1 - self._fury_side
        return [laser]

    # -- FANBLAZE (Boss 2): slow sweeping pendulum ----------------------

    def _fire_fanblaze(self) -> list:
        """Fanblaze: fires 3 parallel lasers that sweep back and forth.

        The spread angle slowly oscillates like a pendulum.  All 3
        lasers share the same angle so the player only needs to move
        laterally to avoid them.  The sweep reverses at ±35 degrees.
        """
        lasers: list[Laser] = []
        center_x = self.x + self.width / 2
        center_y = self.y + self.height

        rad = math.radians(self._fan_angle)
        vx = math.sin(rad) * 4.0
        vy = math.cos(rad) * 5.0

        # 3 parallel lasers with small horizontal offset
        for offset in (-14, 0, 14):
            lasers.append(
                Laser(center_x + offset - 2, center_y, vy, MAGENTA,
                      is_enemy=True, vx=vx),
            )

        # Advance the pendulum
        self._fan_angle += self._fan_sweep_speed * self._fan_dir
        if self._fan_angle > 35:
            self._fan_angle = 35.0
            self._fan_dir = -1
        elif self._fan_angle < -35:
            self._fan_angle = -35.0
            self._fan_dir = 1

        return lasers

    # -- VORTEX (Boss 3): double helix spiral ---------------------------

    def _fire_vortex(self) -> list:
        """Vortex: two opposite spiral arms rotating at constant speed.

        Two lasers are fired 180 degrees apart, creating a double-helix
        pattern.  The rotation speed is constant and moderate, so the
        player can orbit in the same direction to stay safe.
        """
        lasers: list[Laser] = []
        center_x = self.x + self.width / 2
        center_y = self.y + self.height

        for arm_offset in (0, math.pi):
            angle = self._helix_angle + arm_offset
            vx = math.sin(angle) * 3.0
            vy = math.cos(angle) * 3.5 + 2.0  # bias downward
            lasers.append(
                Laser(center_x - 2, center_y, vy, GREEN,
                      is_enemy=True, vx=vx),
            )

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
