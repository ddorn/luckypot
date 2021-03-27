import pygame

from settings import settings


class Object:
    Z = 0

    def __init__(self, pos, size, vel=(0, 0)):
        self.pos = pygame.Vector2(pos)
        self.size = pygame.Vector2(size)
        self.vel = pygame.Vector2(vel)
        self.alive = True

    @property
    def center(self):
        return self.pos + self.size / 2

    @center.setter
    def center(self, value):
        self.pos = value - self.size / 2

    def logic(self, state):
        """Overwrite this to update the object every frame.

        Args:
            state (State): Current state of the app
        """

        self.pos += self.vel

    def draw(self, gfx: 'GFX'):
        if settings.debug:
            gfx.rect(*self.pos, *self.size, 'red', 1)

    def on_death(self, state):
        """Overwrite this to have a logic when the object dies.

        Args:
            state (State): Current state of the app.
        """

    def resize(self, old, new):
        """Called every time the window resizes.

        This should not have any impoact on position/speed,
        as they should not depend on the window size. Instead
        this should handle the different sprite sizes.
        Args:
            old (pygame.Vector2): previous size of the window
            new (pygame.Vector2): actual size of the window
        """

