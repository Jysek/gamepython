#!/usr/bin/env python3
"""
Space Shooter -- Infinite Survival
Authors: Ceccariglia Emanuele & Andrea Cestelli -- ITSUmbria 2026

A 2D arcade shooter inspired by Space Invaders,
developed in Python with Pygame.

Main entry point of the game.
When built with PyInstaller the bundled assets are resolved
automatically via ``core.assets.resource_path()``.
"""

import pygame
from game.game import Game


def main() -> None:
    """Initialize Pygame, load assets and start the game loop."""
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

    # Assets.load() is called inside Game.__init__ after display.set_mode()
    # so that convert_alpha() works correctly.
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
