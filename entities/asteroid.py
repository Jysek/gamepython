"""
Asteroid -- sprite with a luminous pixel-art trail and a guaranteed
safe corridor.

Asteroids fall from top to bottom with rotation and a particle trail
rendered with ``BLEND_ADD`` for a fire/heat glow.

A global registry ``_active_x`` prevents horizontal overlap.  During
asteroid rain events the system guarantees that at least one corridor
of width ``SAFE_CORRIDOR_W`` pixels remains clear.
"""

import random
import pygame

from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, ASTEROID_SIZE
from core.assets import Assets

# ---------------------------------------------------------------------------
# Global registry of active asteroid X positions
# ---------------------------------------------------------------------------
_active_x: list[float] = []
_MIN_GAP = 90  # minimum horizontal separation (px)

# Minimum width of the guaranteed safe corridor during rain
SAFE_CORRIDOR_W = 100

# Trail spritestrip parameters
_N_FRAMES = 12
_FW = 32


def _safe_x(w: int) -> float:
    """Find a safe X position for a new asteroid.

    Tries random placement that respects the minimum distance from all
    active asteroids **and** does not block the largest remaining gap.
    Falls back to a column-based strategy when random attempts fail.

    Args:
        w: Asteroid width in pixels.

    Returns:
        X position as float, or -1 if spawning would block the safe
        corridor (caller should skip the spawn).
    """
    corridor = _find_largest_gap()

    for _ in range(30):
        x = random.randint(20, SCREEN_WIDTH - w - 20)
        if not all(abs(x - ox) >= _MIN_GAP for ox in _active_x):
            continue
        if _would_block_corridor(x, w, corridor):
            continue
        return float(x)

    # Fallback: pick the least-populated column
    cols = 6
    cw = (SCREEN_WIDTH - 40) // cols
    counts = [0] * cols
    for ox in _active_x:
        c = int((ox - 20) / cw)
        if 0 <= c < cols:
            counts[c] += 1

    sorted_cols = sorted(range(cols), key=lambda i: counts[i])
    for best in sorted_cols:
        x = float(20 + best * cw + random.randint(0, max(0, cw - w)))
        if not _would_block_corridor(x, w, corridor):
            return x

    return -1.0  # cannot spawn without blocking corridor


def _find_largest_gap() -> tuple[float, float]:
    """Find the widest horizontal gap between active asteroids.

    Returns:
        ``(gap_start, gap_end)`` of the largest gap.
    """
    if not _active_x:
        return (0.0, float(SCREEN_WIDTH))

    half_w = ASTEROID_SIZE / 2
    intervals = sorted(
        (x - half_w, x + ASTEROID_SIZE + half_w) for x in _active_x
    )

    # Merge overlapping intervals
    merged: list[tuple[float, float]] = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Find the widest gap
    best_gap = (0.0, merged[0][0])
    for i in range(len(merged) - 1):
        gap_start = merged[i][1]
        gap_end = merged[i + 1][0]
        if (gap_end - gap_start) > (best_gap[1] - best_gap[0]):
            best_gap = (gap_start, gap_end)

    final_start = merged[-1][1]
    final_end = float(SCREEN_WIDTH)
    if (final_end - final_start) > (best_gap[1] - best_gap[0]):
        best_gap = (final_start, final_end)

    return best_gap


def _would_block_corridor(
    x: float,
    w: int,
    corridor: tuple[float, float],
) -> bool:
    """Check whether placing an asteroid at *x* would close the corridor.

    A corridor is considered blocked when its remaining width would drop
    below ``SAFE_CORRIDOR_W``.
    """
    gap_w = corridor[1] - corridor[0]
    if gap_w <= SAFE_CORRIDOR_W:
        return True  # already too narrow

    half = ASTEROID_SIZE / 2
    ast_left = x - half
    ast_right = x + w + half

    if ast_right <= corridor[0] or ast_left >= corridor[1]:
        return False  # outside the corridor

    left_gap = max(0, ast_left - corridor[0])
    right_gap = max(0, corridor[1] - ast_right)
    return max(left_gap, right_gap) < SAFE_CORRIDOR_W


def clear_registry() -> None:
    """Clear the global asteroid position registry."""
    _active_x.clear()


class _Particle:
    """Single luminous trail particle for an asteroid.

    Particles drift upward slightly (hot smoke), advance through the
    spritestrip frames and fade out.
    """

    __slots__ = ("x", "y", "vx", "vy", "frame", "alpha", "sz", "alive")

    def __init__(self, cx: float, cy: float) -> None:
        self.x = cx + random.uniform(-10, 10)
        self.y = cy + random.uniform(-6, 6)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-1.0, -0.15)
        self.frame = float(random.randint(0, 2))
        self.alpha = random.randint(200, 255)
        self.sz = random.uniform(0.5, 1.2)
        self.alive = True

    def update(self) -> None:
        """Advance position, animation frame and opacity."""
        self.x += self.vx
        self.y += self.vy
        self.frame += 0.4
        self.alpha -= 16
        self.sz = max(0, self.sz - 0.02)
        if self.alpha <= 0 or self.sz < 0.05 or self.frame >= _N_FRAMES:
            self.alive = False

    def draw(self, surf: pygame.Surface, frames: list[pygame.Surface]) -> None:
        """Render the particle using the trail spritestrip."""
        fi = min(int(self.frame), _N_FRAMES - 1)
        src = frames[fi]
        sz = max(2, int(_FW * self.sz))
        scaled = pygame.transform.scale(src, (sz, sz))
        scaled.set_alpha(max(0, min(255, int(self.alpha))))
        surf.blit(
            scaled,
            (int(self.x - sz // 2), int(self.y - sz // 2)),
            special_flags=pygame.BLEND_ADD,
        )


class Asteroid:
    """Falling asteroid with rotation and a luminous trail.

    Asteroids are indestructible (lasers pass through them).
    Collision without a shield = instant death.
    """

    MIN_SPEED = 1.8
    MAX_SPEED = 3.2

    def __init__(self) -> None:
        self.width = ASTEROID_SIZE
        self.height = ASTEROID_SIZE
        x = _safe_x(self.width)
        if x < 0:
            # Safe corridor would be blocked -- abort spawn
            self.x = 0.0
            self.y = -999.0
            self.active = False
            self.fall_speed = 0.0
            self.angle = 0.0
            self.rot_speed = 0
            self.trail: list[_Particle] = []
            return

        self.x = x
        self.y = float(-self.height - random.randint(0, 40))
        self.active = True
        _active_x.append(self.x)

        self.fall_speed = random.uniform(self.MIN_SPEED, self.MAX_SPEED)
        self.angle = 0.0
        self.rot_speed = random.choice([-3, -2, -1, 1, 2, 3])
        self.trail: list[_Particle] = []

    def update(self) -> None:
        """Update position, rotation and trail particles."""
        if not self.active:
            return

        self.y += self.fall_speed
        self.angle = (self.angle + self.rot_speed) % 360

        # Spawn trail particles
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        for _ in range(random.randint(4, 6)):
            self.trail.append(_Particle(cx, cy))

        for p in self.trail:
            p.update()
        self.trail = [p for p in self.trail if p.alive]

        # Deactivate when off the bottom of the screen
        if self.y > SCREEN_HEIGHT + 60:
            self.active = False
            self._unregister()

    def _unregister(self) -> None:
        """Remove this asteroid's X from the global registry."""
        try:
            _active_x.remove(self.x)
        except ValueError:
            pass

    def deactivate(self) -> None:
        """Explicitly deactivate and unregister the asteroid."""
        if self.active:
            self.active = False
            self._unregister()

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the rotating asteroid with its luminous trail."""
        if not self.active:
            return

        # Trail behind the asteroid
        if Assets.trail_frames:
            for p in self.trail:
                p.draw(surf, Assets.trail_frames)

        # Rotated asteroid sprite
        rot = pygame.transform.rotate(Assets.asteroid_sprite, self.angle)
        rect = rot.get_rect(center=(
            int(self.x + self.width // 2),
            int(self.y + self.height // 2),
        ))
        surf.blit(rot, rect)

    def get_rect(self) -> pygame.Rect:
        """Return the collision hitbox (shrunk 8 px per side)."""
        shrink = 8
        return pygame.Rect(
            self.x + shrink,
            self.y + shrink,
            self.width - shrink * 2,
            self.height - shrink * 2,
        )
