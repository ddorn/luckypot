from functools import lru_cache

import pygame


class GFX:
    def __init__(self, surf: pygame.Surface):
        self.surf = surf
        self.world_center = pygame.Vector2(0, 0)
        """World coordinates that are in the center of the screen."""
        self.world_scale = 16
        """How many pixel is one world unit."""
        self.ui_scale = 1

    def scale_ui_pos(self, x, y):
        return (
            int(x * self.surf.get_width()),
            int(y * self.surf.get_height())
        )

    def scale_world_size(self, w, h):
        return (
            int(w * self.world_scale),
            int(h * self.world_scale)
        )

    @lru_cache(maxsize=2000)
    def scale_surf(self, surf: pygame.Surface, factor):
        if factor == 1:
            return surf
        size = (int(surf.get_width() * factor), int(surf.get_height() * factor))
        return pygame.transform.scale(surf, size)

    def ui_blit(self, surf: pygame.Surface, **anchor):
        assert len(anchor) == 1
        anchor, value = anchor.popitem()

        s = self.scale_surf(surf, self.ui_scale)
        r = s.get_rect(**{anchor: self.scale_ui_pos(*value)})
        self.surf.blit(s, r)

    def world_blit(self, surf, **anchor):
        assert len(anchor) == 1
        anchor, value = anchor.popitem()

        s = self.scale_surf(surf, self.world_scale)
        r = s.get_rect(**{anchor: pygame.Vector2(value) * self.world_scale})
        r.topleft -= self.world_center
        self.surf.blit(s, r)

    def rect(self, x, y, w, h, color, width=0, anchor: str = None):
        """Draw a rectangle in rect coordinates."""
        r = pygame.Rect(x, y, w * self.world_scale, h * self.world_scale)

        if anchor:
            setattr(r, anchor, (x, y))

        pygame.draw.rect(self.surf, color, r, width)

    def fill(self, color):
        self.surf.fill(color)

    def scroll(self, dx, dy):
        self.surf.scroll(dx, dy)

    def to_ui(self, pos):
        """Convert a position in the screen to ui coordinates."""
        return pygame.Vector2(pos) / self.ui_scale

    def to_world(self, pos):
        """Convert a position in the screen to world coordinates."""
        # noinspection PyTypeChecker
        return (pygame.Vector2(pos) - (
            self.surf.get_width() / 2, self.surf.get_height() / 2)) / self.world_scale + self.world_center
