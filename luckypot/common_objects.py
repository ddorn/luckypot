from math import ceil
import pygame

from .constants import WHITE, SMALL_FONT
from .object import Object
from .assets import text
from .utils import auto_crop

__all__ = ["HealthBar"]


class HealthBar(Object):
    """
    A generic health bar that flashes when loosing health.

    It is based on objects having a life and max_life attribute, like Entities for instance.
    """

    Z = 99

    def __init__(self, rect, color, entity, show_hp=False, empty_color=None):
        rect = pygame.Rect(rect)
        super().__init__(rect.topleft, rect.size)

        self.color = pygame.Color(color)
        self.empty_color = pygame.Color(empty_color or (0, 0, 0, self.color.a))
        self.show_hp = show_hp
        self.entity = entity

        self.flash_size = 0
        self.flash_duration = -1
        self.last_health = entity.life

    def logic(self):
        self.flash_duration -= 1

        loss = self.last_health - self.entity.life
        self.flash_size += loss

        if loss > 0:
            self.flash_duration = 10

        if self.flash_duration <= 0:
            self.flash_size -= 1
            self.flash_size *= 0.98
            self.flash_size = max(0, self.flash_size - 3)

        self.last_health = self.entity.life

    def draw(self, gfx: "GFX"):
        prop = self.entity.life / self.entity.max_life
        width = ceil(self.size.x * prop)
        flash = ceil(self.size.x * self.flash_size / self.entity.max_life)
        lost = self.size.x - width - flash

        x, y = self.pos
        gfx.box(self.color, (*self.pos, width, self.size.y))
        if flash > 0:
            gfx.box(WHITE + (self.color.a, ), (x + width, y, flash, self.size.y))

        if lost > 0:
            gfx.box(
                self.empty_color,
                (
                    x + width + flash,
                    y,
                    lost,
                    self.size.y,
                ),
            )

        if self.show_hp:
            t = auto_crop(text(str(int(self.entity.life)), 8, WHITE, SMALL_FONT))
            gfx.blit(t, midleft=self.rect.midleft + pygame.Vector2(2, 0))
