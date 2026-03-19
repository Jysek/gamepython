# Space Shooter -- Infinite Survival v2.0

A 2D arcade shooter inspired by Space Invaders, developed in **Python** with **Pygame**.

**By:** Ceccariglia Emanuele & Andrea Cestelli -- ITSUmbria 2026

---

## Requirements

| Dependency | Minimum version | Install                              |
|------------|-----------------|--------------------------------------|
| Python     | 3.10+           | [python.org](https://www.python.org) |
| Pygame     | 2.0+            | `pip install pygame`                 |
| Pillow     | 9.0+            | `pip install Pillow`                 |

---

## Quick Start

```bash
# Install dependencies
pip install pygame Pillow

# Launch the game
python main.py
```

---

## Controls

| Key                     | Action                              |
|-------------------------|-------------------------------------|
| `W` / Arrow Up          | Move up                             |
| `S` / Arrow Down        | Move down                           |
| `A` / Arrow Left        | Move left                           |
| `D` / Arrow Right       | Move right                          |
| `SPACE`                 | Shoot                               |
| `B`                     | Use bomb                            |
| `F`                     | Special ability (EMP / Overdrive)   |
| `P` / `ESC`             | Pause / Resume                      |
| `ENTER`                 | Confirm selection                   |
| `A` / `D`               | Choose ship (ship select screen)    |

---

## Ships (5 playable)

Five animated ships, each with unique stats and abilities.  The last two have a **double cannon**.

| # | Name        | Cannon       | Special            | Unlock    |
|---|-------------|--------------|--------------------|-----------|
| 0 | **Viper**   | Single       | None               | Default   |
| 1 | **Phoenix** | Single       | HP Regeneration    | 200 pts   |
| 2 | **Striker** | Single       | Piercing lasers    | 500 pts   |
| 3 | **Nova**    | Double       | EMP (key F)        | 1 000 pts |
| 4 | **Zenith**  | Double       | Overdrive (key F)  | 2 000 pts |

### Ship Stats

| Ship    | Speed | Fire Rate    | Damage | Special                        |
|---------|-------|--------------|--------|--------------------------------|
| Viper   | 1.0x  | 1.0x         | 1      | Balanced, no special           |
| Phoenix | 0.8x  | 1.3x (slow)  | 2      | Regen 1 HP every 15 s          |
| Striker | 1.4x  | 0.6x (fast)  | 1      | Lasers pierce through enemies  |
| Nova    | 1.1x  | 0.85x        | 1      | EMP: clears enemy lasers       |
| Zenith  | 0.9x  | 1.0x         | 2      | Overdrive: rapid fire for 5 s  |

---

## Enemies (4 animated types)

| Type        | HP | Points | Fire pattern               |
|-------------|----|--------|----------------------------|
| **Scout**   | 1  | 1      | Fast single laser          |
| **Fighter** | 2  | 3      | Double parallel lasers     |
| **Bomber**  | 4  | 5      | Slow triple parallel       |
| **Elite**   | 3  | 8      | Rapid 3-burst              |

### Intelligent Formations
Formations contain **mixed types**: scouts in the front rows, bombers and elites in the back.  18 formation patterns are available, chosen with an anti-repetition system.

### Hit Feedback (multi-HP enemies)
- **Shake**: rapid sprite oscillation
- **Mini-explosion**: animated impact flash
- **HP bar**: shows remaining health

---

## Boss Fight (4 variants)

Each boss has a unique **animated GIF** and an exclusive **fire pattern**.  Boss selection is **random with equal probability**.

| # | Name          | Pattern                                        |
|---|---------------|------------------------------------------------|
| 0 | **Titan**     | Rotating cannons: straight, converging, aimed  |
| 1 | **Fury**      | Devastating bursts + auto secondary fire       |
| 2 | **Fanblaze**  | Alternating fan waves with variable spread     |
| 3 | **Vortex**    | 3 spiral arms that accelerate gradually        |

### Progressive Scaling
Each successive boss gets stronger:
- +10 HP per boss defeated
- +0.3 horizontal speed
- -4 frames shoot interval (min 22)
- Increasing score bonus

---

## Game Mechanics

### Combo System
Kill enemies in rapid succession to build combos:
- 3+ kills: combo visible
- Score multiplier: +50 %, +100 %, +150 %, +200 %, +300 %
- Floating damage numbers on screen

### Bombs
- Collect from the Bomb power-up (max 3)
- Destroys ALL enemies on screen and clears enemy lasers
- Deals 25 % of the boss's remaining HP
- 2-second cooldown between uses

### Slow Motion
- Activates automatically after a boss defeat
- Slows the action for a dramatic moment

### Lives & Protection
- 3 maximum lives
- Temporary invincibility after each hit
- Shield absorbs hits and protects from damage
- Asteroid with shield: shield breaks, no HP loss
- Asteroid without shield: instant death

---

## Power-Ups

Power-ups are carried by **carrier ships** that descend and hover for 5 seconds.

| Type       | Effect                       | Duration    |
|------------|------------------------------|-------------|
| **Health** | Restore 1 heart (max 3)     | Instant     |
| **Shield** | Absorb incoming hits         | 5 seconds   |
| **Speed**  | Speed boost x1.8             | 5 seconds   |
| **Weapon** | Triple / quad angled shot    | 5 seconds   |
| **Bomb**   | +1 bomb (max 3)             | Permanent   |

---

## Formations (18 patterns)

Randomly chosen with anti-repetition:

`H_LINE_3`, `H_LINE_5`, `V_LINE_3`, `GRID_3x2`, `GRID_4x2`, `GRID_3x3`,
`DIAMOND`, `V_SHAPE`, `CROSS`, `T_SHAPE`, `STAGGER_3x2`,
`PINCER`, `ARROW`, `Z_LINE`, `WING`, `CHEVRON`, `FORTRESS`, `X_SHAPE`

---

## Asteroids

- Fall vertically with a **luminous trail** (animated spritestrip)
- **Indestructible** by lasers
- Collision without shield = **instant death**
- Shield absorbs ONE asteroid hit

### Asteroid Rain
Periodic special event:
1. **3-second warning** with flashing orange overlay
2. Asteroids rain down for 20--40 seconds
3. **Guaranteed safe corridor**: at least 100 px clear

---

## Progressive Difficulty

Every **30 seconds** the difficulty increases (max level 10):
- Enemies +12 % speed per level
- Shorter spawn intervals
- More enemies per wave
- More complex formations
- Stronger enemy types unlocked

---

## Audio

All sounds -- including the **background music** -- are generated
**procedurally at runtime** without any external audio files.

---

## Save System

The game auto-saves to `save_data.json`:
- All-time high score
- Top 10 scores
- Unlocked ships (progressive unlock)
- Cumulative stats (playtime, kills, bosses defeated)

Automatic migration from earlier save formats is supported.

---

## Project Structure

```
SpaceShooter/
|-- main.py                     # Entry point
|-- save_data.json              # Auto-save file
|-- .gitignore
|-- README.md
|
|-- core/                       # Shared infrastructure
|   |-- __init__.py
|   |-- assets.py               # Centralised asset loader (GIF/PNG -> Pygame)
|   |-- constants.py            # Global constants (ships, bosses, colours, etc.)
|   |-- save_manager.py         # JSON save / load / migration
|   +-- sounds.py               # Procedural audio + background music
|
|-- entities/                   # Game entities
|   |-- __init__.py
|   |-- player.py               # Player ship (5 ships, animated, abilities)
|   |-- enemy.py                # Enemy with animated GIF sprite + shake
|   |-- boss.py                 # Boss with 4 variants + unique fire patterns
|   |-- asteroid.py             # Asteroid with safe-corridor logic
|   |-- laser.py                # Straight / angled laser projectiles
|   |-- powerup.py              # Carrier + falling power-up items
|   |-- explosion.py            # Animated explosion from GIF
|   |-- formations.py           # 18 formations with anti-repetition
|   +-- formation_group.py      # Enemy group with mixed types (weak front)
|
|-- game/
|   |-- __init__.py
|   +-- game.py                 # Game loop, states, spawning, collisions, HUD
|
|-- world/
|   |-- __init__.py
|   +-- starfield.py            # 3-layer parallax star field
|
+-- assets/                     # Sprites (PNG and GIF)
    |-- ships/                  # Player ship spritesheets
    |-- enemies/                # Enemy spritesheets
    |-- bosses/                 # Boss animated GIFs (4 variants)
    |-- lasers/                 # 66 laser sprite variants
    |-- powerups/               # Carrier + power-up sprites
    |-- sprites/                # Asteroids and trails
    +-- effects/                # Explosion GIF
```

---

*Developed with Python 3 / Pygame / Pillow -- ITSUmbria 2026*
