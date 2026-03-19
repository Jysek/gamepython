"""
Player ship -- animated sprite with lives, invincibility, power-ups
and special abilities.

Five playable ships with unique stats and abilities.  The last two
(Nova, Zenith) feature a double cannon.  Ships with a special ability
expose ``special_cooldown_pct`` for the HUD cooldown bar.
"""

import math
import random
import pygame

from core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_W, PLAYER_H,
    CYAN, SHIP_COLORS, NUM_PLAYER_SHIPS,
    SHIP_STATS, SHIP_DOUBLE_CANNON, SPECIAL_COOLDOWNS,
)
from core.assets import Assets
from entities.laser import Laser, AngledLaser


class Player:
    """Player ship with lives, power-ups, special abilities and shooting.

    Args:
        ship_type: Index of the chosen ship (0--4).
    """

    MAX_LIVES = 3

    def __init__(self, ship_type: int = 0) -> None:
        self.width = PLAYER_W
        self.height = PLAYER_H
        self.x: float = SCREEN_WIDTH // 2 - self.width // 2
        self.y: float = SCREEN_HEIGHT - 80
        self.ship_type = ship_type % NUM_PLAYER_SHIPS

        # Ship-specific stats
        stats = SHIP_STATS[self.ship_type]
        self.base_speed = int(5 * stats["speed"])
        self.speed = self.base_speed
        self.shot_cooldown = int(300 * stats["fire_rate"])
        self.damage: int = stats.get("damage", 1)
        self.special: str = stats.get("special", "none")

        # Double cannon: only for flagged ships
        self.has_double_cannon = (
            self.ship_type < len(SHIP_DOUBLE_CANNON)
            and SHIP_DOUBLE_CANNON[self.ship_type]
        )

        self.last_shot_time = 0
        self.alive = True

        # Lives
        self.lives = Player.MAX_LIVES

        # Ship colour (used for laser tint and HUD)
        self.color = SHIP_COLORS[self.ship_type % len(SHIP_COLORS)]

        # Vertical movement limit (cannot go higher than top third)
        self.min_y = SCREEN_HEIGHT // 3

        # Temporary invincibility after taking damage
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 2 * 60  # 2 seconds at 60 FPS

        # -- POWER-UP STATE --
        self.shield_active = False
        self.shield_timer = 0
        self.shield_duration = 5 * 60

        self.speed_boost_active = False
        self.speed_boost_timer = 0
        self.speed_boost_duration = 5 * 60
        self.speed_boost_multiplier = 1.8

        self.triple_shot_active = False
        self.triple_shot_timer = 0
        self.triple_shot_duration = 5 * 60

        # Bombs
        self.bombs = 0
        self.max_bombs = 3
        self.bomb_cooldown = 0
        self.bomb_cooldown_max = 120  # 2 seconds

        # Special ability cooldowns
        self.special_cooldown = 0
        self.special_active = False
        self.special_timer = 0

        # Regen (Phoenix): restore 1 HP every 15 s
        self._regen_timer = 0
        self._regen_interval = SPECIAL_COOLDOWNS.get("regen", 15 * 60)

        # Piercing (Striker): lasers pass through enemies
        self.piercing_shots = (self.special == "piercing")

        # EMP (Nova)
        self.emp_cooldown = 0
        self.emp_max_cooldown = SPECIAL_COOLDOWNS.get("emp", 20 * 60)
        self.emp_ready = True  # starts ready

        # Overdrive (Zenith): temporary rapid fire
        self.overdrive_active = False
        self.overdrive_timer = 0
        self.overdrive_duration = 5 * 60
        self.overdrive_cooldown = 0
        self.overdrive_max_cooldown = SPECIAL_COOLDOWNS.get("overdrive", 30 * 60)

        # GIF animation state
        self._frame_idx = 0
        self._frame_timer = 0
        self._frame_delay = 6

        # Engine trail particles (visual effect)
        self._engine_particles: list[dict] = []

    # ========================================================================
    # SPECIAL COOLDOWN PERCENTAGE (for HUD bar)
    # ========================================================================

    @property
    def special_cooldown_pct(self) -> float:
        """Return 0.0 .. 1.0 representing how charged the special is.

        1.0 means fully charged (ready).  0.0 means just used.
        Ships with ``special == 'none'`` always return -1 (no bar).
        """
        if self.special == "none":
            return -1.0

        if self.special == "regen":
            # Show regen timer progress (fills up between heals)
            if self.lives >= Player.MAX_LIVES:
                return 1.0
            return self._regen_timer / max(1, self._regen_interval)

        if self.special == "piercing":
            # Piercing is always-on passive -- no cooldown bar
            return -1.0

        if self.special == "emp":
            if self.emp_ready:
                return 1.0
            return 1.0 - (self.emp_cooldown / max(1, self.emp_max_cooldown))

        if self.special == "overdrive":
            if self.overdrive_active:
                # During overdrive: show remaining active time
                return self.overdrive_timer / max(1, self.overdrive_duration)
            if self.overdrive_cooldown > 0:
                return 1.0 - (self.overdrive_cooldown / max(1, self.overdrive_max_cooldown))
            return 1.0

        return -1.0

    @property
    def special_label(self) -> str:
        """Return a short label describing the current special state."""
        labels = {
            "none": "",
            "regen": "REGEN",
            "piercing": "",
            "emp": "EMP",
            "overdrive": "OVERDRIVE",
        }
        return labels.get(self.special, "")

    @property
    def special_is_ready(self) -> bool:
        """Return True if the special ability is ready to activate."""
        if self.special == "emp":
            return self.emp_ready
        if self.special == "overdrive":
            return not self.overdrive_active and self.overdrive_cooldown <= 0
        return False

    # ========================================================================
    # UPDATE
    # ========================================================================

    def update(self, keys) -> None:
        """Update position, power-up timers, invincibility and animation."""
        if not self.alive:
            return

        self._update_powerup_timers()
        self._update_special_timers()

        # Invincibility countdown
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        current_speed = self.speed

        # WASD / arrow-key movement
        dx, dy = 0.0, 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += current_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= current_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += current_speed

        # Normalise diagonal speed
        if dx != 0 and dy != 0:
            factor = 0.707  # 1 / sqrt(2)
            dx *= factor
            dy *= factor

        self.x += dx
        self.y += dy

        # Clamp to screen boundaries
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(self.min_y, min(SCREEN_HEIGHT - self.height, self.y))

        # Advance GIF animation
        self._frame_timer += 1
        if self._frame_timer >= self._frame_delay:
            self._frame_timer = 0
            frames = self._get_frames()
            if frames:
                self._frame_idx = (self._frame_idx + 1) % len(frames)

        # Update engine trail particles
        self._update_engine_particles()

    def _update_powerup_timers(self) -> None:
        """Tick down active power-up durations."""
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

        if self.speed_boost_active:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost_active = False
                self.speed = self.base_speed

        if self.triple_shot_active:
            self.triple_shot_timer -= 1
            if self.triple_shot_timer <= 0:
                self.triple_shot_active = False

        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1

    def _update_special_timers(self) -> None:
        """Tick down special-ability cooldowns and effects."""
        # Phoenix: passive HP regen
        if self.special == "regen":
            if self.lives < Player.MAX_LIVES:
                self._regen_timer += 1
                if self._regen_timer >= self._regen_interval:
                    self._regen_timer = 0
                    self.lives = min(Player.MAX_LIVES, self.lives + 1)
            else:
                # Reset timer when at full HP so bar shows full
                self._regen_timer = 0

        # Nova: EMP cooldown
        if self.special == "emp":
            if self.emp_cooldown > 0:
                self.emp_cooldown -= 1
                if self.emp_cooldown <= 0:
                    self.emp_ready = True

        # Zenith: Overdrive duration / cooldown
        if self.special == "overdrive":
            if self.overdrive_active:
                self.overdrive_timer -= 1
                if self.overdrive_timer <= 0:
                    self.overdrive_active = False
                    self.overdrive_cooldown = self.overdrive_max_cooldown
            elif self.overdrive_cooldown > 0:
                self.overdrive_cooldown -= 1

    def _update_engine_particles(self) -> None:
        """Spawn and update engine-trail particles behind the ship."""
        if self.alive:
            cx = self.x + self.width // 2
            by = self.y + self.height
            self._engine_particles.append({
                "x": cx + random.uniform(-6, 6),
                "y": by + random.uniform(0, 4),
                "alpha": 180,
                "size": random.uniform(1.5, 3.5),
            })

        new_particles: list[dict] = []
        for p in self._engine_particles:
            p["y"] += 1.5
            p["alpha"] -= 12
            p["size"] = max(0, p["size"] - 0.08)
            if p["alpha"] > 0 and p["size"] > 0:
                new_particles.append(p)
        self._engine_particles = new_particles[-30:]  # cap at 30

    def _get_frames(self) -> list[pygame.Surface]:
        """Return the animated frames for the current ship type."""
        if self.ship_type < len(Assets.player_ship_frames):
            return Assets.player_ship_frames[self.ship_type]
        return []

    # ========================================================================
    # POWER-UPS
    # ========================================================================

    def apply_powerup(self, powerup_type: str) -> None:
        """Apply the effect of a collected power-up."""
        if powerup_type == "vita":
            if self.lives < Player.MAX_LIVES:
                self.lives += 1
        elif powerup_type == "scudo":
            self.shield_active = True
            self.shield_timer = self.shield_duration
        elif powerup_type == "velocita":
            self.speed_boost_active = True
            self.speed_boost_timer = self.speed_boost_duration
            self.speed = self.base_speed * self.speed_boost_multiplier
        elif powerup_type == "arma":
            self.triple_shot_active = True
            self.triple_shot_timer = self.triple_shot_duration
        elif powerup_type == "bomba":
            self.bombs = min(self.max_bombs, self.bombs + 1)

    # ========================================================================
    # BOMBS
    # ========================================================================

    def use_bomb(self) -> bool:
        """Attempt to use a bomb.  Returns True if one was used."""
        if self.bombs > 0 and self.bomb_cooldown <= 0:
            self.bombs -= 1
            self.bomb_cooldown = self.bomb_cooldown_max
            return True
        return False

    # ========================================================================
    # SPECIAL ABILITIES
    # ========================================================================

    def activate_emp(self) -> bool:
        """Activate EMP (Nova only).  Returns True if activated."""
        if self.special == "emp" and self.emp_ready:
            self.emp_ready = False
            self.emp_cooldown = self.emp_max_cooldown
            return True
        return False

    def activate_overdrive(self) -> bool:
        """Activate Overdrive (Zenith only).  Returns True if activated."""
        if (self.special == "overdrive"
                and not self.overdrive_active
                and self.overdrive_cooldown <= 0):
            self.overdrive_active = True
            self.overdrive_timer = self.overdrive_duration
            return True
        return False

    # ========================================================================
    # DAMAGE
    # ========================================================================

    def take_damage(self) -> bool:
        """Inflict one point of damage on the player.

        Returns:
            True if the player has died (0 lives remaining).
        """
        if self.invincible or self.shield_active:
            return False

        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.alive = False
            return True

        self.invincible = True
        self.invincible_timer = self.invincible_duration
        return False

    # ========================================================================
    # SHOOTING
    # ========================================================================

    def shoot(self, current_time: int) -> list[Laser]:
        """Fire lasers.  Double-cannon ships fire from both sides.

        Args:
            current_time: ``pygame.time.get_ticks()`` value.

        Returns:
            List of newly spawned ``Laser`` objects (may be empty).
        """
        if not self.alive:
            return []

        cooldown = self.shot_cooldown
        if self.overdrive_active:
            cooldown //= 2

        if current_time - self.last_shot_time < cooldown:
            return []

        self.last_shot_time = current_time
        sprite = Assets.laser_sprites[self.ship_type % len(Assets.laser_sprites)]

        if self.has_double_cannon:
            return self._shoot_double(sprite)
        return self._shoot_standard(sprite)

    def _shoot_double(self, sprite: pygame.Surface) -> list[Laser]:
        """Fire two parallel lasers from the ship's sides."""
        cannon_offset = 16
        center_x = self.x + self.width // 2 - 10

        lasers: list[Laser] = [
            Laser(center_x - cannon_offset, self.y, -7, self.color, sprite=sprite),
            Laser(center_x + cannon_offset, self.y, -7, self.color, sprite=sprite),
        ]

        if self.triple_shot_active:
            left_spr = Assets.laser_left_angular[
                self.ship_type % len(Assets.laser_left_angular)
            ]
            right_spr = Assets.laser_right_angular[
                self.ship_type % len(Assets.laser_right_angular)
            ]
            lasers.extend([
                AngledLaser(center_x - cannon_offset, self.y, -7, -45,
                            self.color, sprite=left_spr),
                AngledLaser(center_x + cannon_offset, self.y, -7, 45,
                            self.color, sprite=right_spr),
            ])

        return lasers

    def _shoot_standard(self, sprite: pygame.Surface) -> list[Laser]:
        """Fire a single laser from the ship's centre."""
        center_x = self.x + self.width // 2 - 10
        lasers: list[Laser] = [
            Laser(center_x, self.y, -7, self.color, sprite=sprite),
        ]

        if self.triple_shot_active:
            left_spr = Assets.laser_left_angular[
                self.ship_type % len(Assets.laser_left_angular)
            ]
            right_spr = Assets.laser_right_angular[
                self.ship_type % len(Assets.laser_right_angular)
            ]
            lasers.extend([
                AngledLaser(center_x, self.y, -7, -45, self.color, sprite=left_spr),
                AngledLaser(center_x, self.y, -7, 45, self.color, sprite=right_spr),
            ])

        return lasers

    # ========================================================================
    # DRAW
    # ========================================================================

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the animated ship with visual effects."""
        if not self.alive:
            return

        # Engine trail
        self._draw_engine_trail(surface)

        # Invincibility blink
        if self.invincible and (self.invincible_timer // 4) % 2 == 0:
            pass  # invisible frame
        else:
            frames = self._get_frames()
            if frames:
                frame = frames[self._frame_idx % len(frames)]
                scaled_ship = pygame.transform.scale(frame, (self.width, self.height))
            else:
                scaled_ship = pygame.Surface(
                    (self.width, self.height), pygame.SRCALPHA,
                )
                pygame.draw.rect(
                    scaled_ship, self.color,
                    (0, 0, self.width, self.height),
                )

            # Overdrive: golden tint overlay
            if self.overdrive_active:
                overlay = pygame.Surface(
                    (self.width, self.height), pygame.SRCALPHA,
                )
                alpha = int(abs(math.sin(self.overdrive_timer * 0.15)) * 60) + 30
                overlay.fill((255, 215, 0, alpha))
                scaled_ship.blit(overlay, (0, 0), special_flags=pygame.BLEND_ADD)

            surface.blit(scaled_ship, (int(self.x), int(self.y)))

        # Shield bubble
        if self.shield_active:
            self._draw_shield(surface)

    def _draw_engine_trail(self, surface: pygame.Surface) -> None:
        """Render engine-trail particles."""
        for p in self._engine_particles:
            size = max(1, int(p["size"]))
            alpha = max(0, min(255, int(p["alpha"])))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            r, g, b = self.color
            pygame.draw.circle(s, (r, g, b, alpha), (size, size), size)
            surface.blit(
                s, (int(p["x"] - size), int(p["y"] - size)),
                special_flags=pygame.BLEND_ADD,
            )

    def _draw_shield(self, surface: pygame.Surface) -> None:
        """Draw the shield bubble and remaining-time bar."""
        shield_alpha = int(abs(math.sin(self.shield_timer * 0.1)) * 60) + 60
        shield_radius = max(self.width, self.height) // 2 + 10

        shield_surf = pygame.Surface(
            (shield_radius * 2, shield_radius * 2), pygame.SRCALPHA,
        )
        pygame.draw.circle(
            shield_surf, (0, 200, 255, shield_alpha),
            (shield_radius, shield_radius), shield_radius, 3,
        )
        pygame.draw.circle(
            shield_surf, (0, 200, 255, shield_alpha // 3),
            (shield_radius, shield_radius), shield_radius - 3,
        )

        cx = self.x + self.width // 2 - shield_radius
        cy = self.y + self.height // 2 - shield_radius
        surface.blit(shield_surf, (int(cx), int(cy)))

        # Remaining-time bar
        bar_w = self.width
        bar_x = self.x
        bar_y = self.y - 8
        pct = self.shield_timer / self.shield_duration
        pygame.draw.rect(surface, (40, 40, 40), (int(bar_x), int(bar_y), bar_w, 3))
        pygame.draw.rect(surface, CYAN, (int(bar_x), int(bar_y), int(bar_w * pct), 3))

    def get_rect(self) -> pygame.Rect:
        """Return the player hitbox (shrunk for fairness)."""
        shrink = 8
        return pygame.Rect(
            self.x + shrink,
            self.y + shrink,
            self.width - shrink * 2,
            self.height - shrink * 2,
        )
