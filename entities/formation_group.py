"""
FormationGroup -- group of enemies that move as a unit.

Each group contains mixed enemy types: weak enemies (scouts) in the
front rows and strong enemies (bombers, elites) in the back rows.
The available types are gated by the current difficulty level.
"""

import random
import pygame

from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, ENEMY_TYPE_STATS
from entities.enemy import Enemy
from entities.formations import Slot

# ---------------------------------------------------------------------------
# Group descent parameters
# ---------------------------------------------------------------------------
DROP_AMOUNT = 22    # pixels per descent step
DROP_INTERVAL = 75  # frames between steps

# ---------------------------------------------------------------------------
# Enemy type assignment per row.
# Row 0 (front) = scouts; higher rows = stronger types.
# ---------------------------------------------------------------------------
_ROW_TYPE_MAP: dict[int, list[str]] = {
    0: ["scout"],
    1: ["scout", "fighter"],
    2: ["fighter", "bomber"],
    3: ["bomber", "elite"],
}

# Types unlocked per difficulty level
_DIFFICULTY_TYPES: list[list[str]] = [
    ["scout"],
    ["scout", "fighter"],
    ["scout", "fighter", "bomber"],
    ["scout", "fighter", "bomber", "elite"],
]

# Quick lookup tables
_SCORE: dict[str, int] = {k: v["score"] for k, v in ENEMY_TYPE_STATS.items()}
_HP: dict[str, int] = {k: v["hp"] for k, v in ENEMY_TYPE_STATS.items()}


def _pick_enemy_type(row: int, difficulty: int) -> str:
    """Select an enemy type based on the formation row and difficulty.

    Front rows get weak enemies; back rows get strong ones.  The
    difficulty level gates which types are available.

    Args:
        row:        Row index (0 = front / lowest in formation).
        difficulty: Current difficulty level.

    Returns:
        Enemy type string.
    """
    diff_idx = min(difficulty, len(_DIFFICULTY_TYPES) - 1)
    available = _DIFFICULTY_TYPES[diff_idx]

    row_types = _ROW_TYPE_MAP.get(row, ["fighter", "bomber", "elite"])

    candidates = [t for t in row_types if t in available]
    if not candidates:
        candidates = [available[0]]

    return random.choice(candidates)


class FormationGroup:
    """Group of enemies in formation that moves as a unit.

    Formations use mixed enemy types: weaker enemies in the front rows
    and stronger ones in the back.

    Args:
        spawn_data:     List of dicts with ``'x'``, ``'y'``, ``'slot'``.
        speed_mult:     Speed multiplier (scales with difficulty).
        formation_name: Name of the chosen formation.
        difficulty:     Current difficulty level.
    """

    def __init__(
        self,
        spawn_data: list[dict],
        speed_mult: float = 1.0,
        formation_name: str = "",
        difficulty: int = 0,
    ) -> None:
        self.formation_name = formation_name

        max_row = max((d["slot"].row for d in spawn_data), default=0)

        self.enemies: list[Enemy] = []
        for d in spawn_data:
            slot: Slot = d["slot"]
            # Invert: slot row 0 is topmost (back), max_row is front
            front_row = max_row - slot.row
            enemy_type = _pick_enemy_type(front_row, difficulty)
            hp = _HP.get(enemy_type, 1)

            enemy = Enemy(d["x"], d["y"], enemy_type=enemy_type, hp=hp)
            enemy.slot = slot
            self.enemies.append(enemy)

        # Horizontal speed (scaled by difficulty)
        base_speed = random.choice([-1.0, -0.7, 0.7, 1.0]) * speed_mult
        self.dx = base_speed

        # Periodic descent timer
        self._drop_timer = 0

        # Cached alive list
        self._cached_alive: list[Enemy] = list(self.enemies)

        # Pending lasers (filled during update)
        self.pending_lasers: list = []

    # ------------------------------------------------------------------
    # Quick-access properties
    # ------------------------------------------------------------------

    @property
    def alive_enemies(self) -> list[Enemy]:
        """Return the cached list of living enemies."""
        return self._cached_alive

    def _refresh_alive_cache(self) -> None:
        """Rebuild the alive-enemies cache."""
        self._cached_alive = [e for e in self.enemies if e.alive]

    @property
    def is_empty(self) -> bool:
        """True when every enemy in the group is dead."""
        return all(not e.alive for e in self.enemies)

    @property
    def left_edge(self) -> float:
        alive = self.alive_enemies
        return min(e.x for e in alive) if alive else 0.0

    @property
    def right_edge(self) -> float:
        alive = self.alive_enemies
        return max(e.x + e.width for e in alive) if alive else 0.0

    @property
    def bottom_edge(self) -> float:
        alive = self.alive_enemies
        return max(e.y + e.height for e in alive) if alive else 0.0

    @property
    def top_edge(self) -> float:
        alive = self.alive_enemies
        return min(e.y for e in alive) if alive else 0.0

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update(self) -> bool:
        """Update the group: movement, shooting and bounds checking.

        Returns:
            True if the bottom edge has reached the screen floor.
        """
        self.pending_lasers.clear()
        self._refresh_alive_cache()

        if not self._cached_alive:
            return False

        # Horizontal movement with edge bounce
        if self.dx < 0 and self.left_edge + self.dx < 10:
            self.dx = abs(self.dx)
        elif self.dx > 0 and self.right_edge + self.dx > SCREEN_WIDTH - 10:
            self.dx = -abs(self.dx)

        for e in self.alive_enemies:
            e.x += self.dx

        # Periodic descent
        self._drop_timer += 1
        if self._drop_timer >= DROP_INTERVAL:
            self._drop_timer = 0
            for e in self.alive_enemies:
                e.y += DROP_AMOUNT

        # Per-enemy shooting
        for e in self.alive_enemies:
            e.shoot_timer += 1
            if e.shoot_timer >= e.shoot_interval:
                e.shoot_timer = 0
                lo, hi = {
                    "scout": (70, 160),
                    "fighter": (100, 200),
                    "bomber": (160, 320),
                    "elite": (80, 180),
                }.get(e.enemy_type, (100, 200))
                e.shoot_interval = random.randint(lo, hi)
                self.pending_lasers.extend(e.build_lasers())

        return self.bottom_edge >= SCREEN_HEIGHT

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface) -> None:
        """Draw every living enemy in the group."""
        for e in self.alive_enemies:
            e.draw(surf)

    # ------------------------------------------------------------------
    # COLLISIONS
    # ------------------------------------------------------------------

    def get_alive_rects(self) -> list[tuple[pygame.Rect, Enemy]]:
        """Return ``(hitbox, enemy)`` pairs for all living enemies."""
        return [(e.get_rect(), e) for e in self.alive_enemies]

    def get_score_for_enemy(self, enemy: Enemy) -> int:
        """Return the score value for killing a specific enemy."""
        return _SCORE.get(enemy.enemy_type, 1)
