from typing import Callable, Dict

from pygame.locals import *

from .assets import *
from .constants import *
from .gfx import GFX
from .object import Object, SpriteObject
from .pygame_input import *
from .utils import *

__all__ = ["Title", "Menu", "Text"]


class Title(Object):
    """Animated text for level transitions or deaths..."""

    Z = 10

    def __init__(self, text, color=YELLOW, duration=4 * 60, animation="enlarge"):
        self.duration = duration
        self.color = color
        self.bg_rect = pygame.Rect(0, 0, 0, 3)

        surf = font(42).render(text, True, color)
        rect = surf.get_rect(center=WORLD.center)

        self.text_surf = surf
        self.shown_image = pygame.Surface((0, 0))
        super().__init__(rect.topleft, surf.get_size())
        self.scripts = {getattr(self, animation)()}

    def enlarge(self):
        widen_frames = 40
        for i in range(widen_frames):
            self.bg_rect.width = (WORLD.width + 2) * chrange(i, (0, widen_frames - 1), (0, 1))
            self.bg_rect.center = self.center
            yield

        larger_frames = 20
        for i in range(larger_frames):
            self.bg_rect.height = (self.size.y + 10) * chrange(i, (0, larger_frames - 1), (0, 1))
            self.bg_rect.center = self.center
            yield

        text_appear_frames = 40
        for i in range(text_appear_frames):
            r = self.text_surf.get_rect()
            r.inflate_ip(-r.w * chrange(i, (0, text_appear_frames), (0, 1), flipped=True), 0)
            self.shown_image = self.text_surf.subsurface(r)
            yield

        for i in range(self.duration):
            # if i % 30 < 20:
            self.shown_image = self.text_surf
            # else:
            #     self.shown_image = pygame.Surface((0, 0))
            yield

        for i in range(larger_frames):
            self.bg_rect.height = (self.size.y + 10) * chrange(i, (0, larger_frames - 1), (0, 1),
                                                               flipped=True)
            self.bg_rect.center = self.center
            self.shown_image = self.text_surf.subsurface(self.text_surf.get_rect().inflate(
                0,
                -self.size.y * chrange(i, (0, larger_frames - 1), (0, 1)),
            ))
            yield

        for i in range(widen_frames):
            self.bg_rect.width = (WORLD.width + 2) * chrange(i, (0, widen_frames - 1), (0, 1),
                                                             flipped=True)
            self.bg_rect.center = self.center
            yield

    def blink(self):
        for i in range(self.duration):
            if i % 60 < 45:
                self.shown_image = self.text_surf
            else:
                self.shown_image = pygame.Surface((0, 0))
            yield

    def logic(self):
        super().logic()

        if not self.scripts:
            self.alive = False

    def draw(self, gfx: GFX):
        super().draw(gfx)
        gfx.box((0, 0, 0, 80), self.bg_rect)
        gfx.rect(self.color, *self.bg_rect, 1)
        gfx.blit(self.shown_image, center=self.center)


class Menu(Object):
    """Simple menu to choose a callback."""

    Z = 10

    def __init__(self, midtop, actions: Dict[str, Callable[[], None]]):
        super().__init__((0, 0))

        self.draw_midtop = midtop
        self.actions = actions
        # We store the selection with an integer, using the fact
        # that dicts are always sorted since 3.6.
        self.selected = 0

    def create_inputs(self):
        up = Button(
            K_UP,
            K_w,
            JoyAxisTrigger(JOY_VERT_RIGHT, -0.5, False),
            JoyAxisTrigger(JOY_VERT_LEFT, -0.5, False),
        )
        up.on_press(lambda _: self.change_selection(-1))

        down = Button(K_DOWN, K_s, JoyAxisTrigger(JOY_VERT_RIGHT), JoyAxisTrigger(JOY_VERT_LEFT))
        down.on_press(lambda _: self.change_selection(+1))

        select = Button(
            K_SPACE,
            K_RETURN,
            K_RIGHT,
            K_d,
            JoyButton(JOY_A),
            JoyButton(JOY_START),
            JoyAxisTrigger(JOY_RT, 0),
            JoyAxisTrigger(JOY_RL, 0),
        )
        select.on_press(self.select)

        return {up: up, down: down, select: select}

    def change_selection(self, amount):
        self.selected += amount
        self.selected %= len(self.actions)

        play("menu")

    def select(self, *_args):
        key = list(self.actions)[self.selected]
        self.actions[key]()

        play("menu")

    def draw(self, gfx: GFX):
        super().draw(gfx)

        midtop = self.draw_midtop
        for i, action in enumerate(self.actions):
            if i == self.selected:
                color = YELLOW
            else:
                color = "white"

            s = text(action, 32, color)
            r = s.get_rect(midtop=midtop)
            gfx.surf.blit(s, r)
            midtop = r.midbottom


class Text(SpriteObject):
    """Simple text object.

    For when it is simpler to have an independant object
    instead of bliting text in .draw() calls.
    """

    Z = 10

    def __init__(self, txt, color, size: int, font_name=None, **anchor):
        img = text(txt, size, color, font_name)
        pos = img.get_rect(**anchor).topleft

        super().__init__(pos, img, size=img.get_size())
