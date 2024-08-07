from math import ceil, sqrt
from random import choice, shuffle, uniform
from typing import Callable, List

from .constants import *
from .gfx import GFX
from .state_machine import State


class StateTransition(State):
    """Base class for all transitions between two states.

    A transition is a visual effect that blends the image of one state into the other.
    """

    def __init__(self, previous: State, next_: State, duration: int | None = None):
        if duration is None:
            duration = 60

        super().__init__()
        self.previous = previous
        self.next = next_
        self.duration = duration  # frames

    def next_surface(self, gfx):
        """Get the screen that the next state would draw."""

        next_surface = pygame.Surface(gfx.surf.get_size())
        self.next.draw(GFX(next_surface))
        return next_surface

    def logic(self):
        super().logic()
        if self.progress == 1:
            self.replace_state(self.next)

    @property
    def progress(self):
        return min(1, self.timer / self.duration)


class FadeTransition(StateTransition):

    def __init__(self, previous, next_, duration=None):
        super().__init__(previous, next_, duration)

    def draw(self, gfx: "GFX"):
        super().draw(gfx)

        self.previous.draw(gfx)

        next_surface = self.next_surface(gfx)

        next_surface.set_alpha(int(255 * self.progress))
        gfx.blit(next_surface)


class SquareSpawnTransition(StateTransition):

    def __init__(self, previous: State, next_: State, square_size=30, delay=64, grow_duration=0):
        self.square_size = square_size  # pixels
        self.delay = delay
        self.grow_duration = grow_duration or square_size

        self.squares = self.spawn_squares()

        duration = max(self.squares) + 2 * self.square_size + self.delay
        super().__init__(previous, next_, duration)

    def square_count(self):
        return self.square_rows() * self.square_cols()

    def square_rows(self):
        return ceil(W / self.square_size)

    def square_cols(self):
        return ceil(H / self.square_size)

    def to_xy(self, idx):
        return divmod(idx, self.square_cols())

    def spawn_squares(self) -> List[int]:
        l = list(range(self.square_count()))
        shuffle(l)
        return l

    def draw(self, gfx: "GFX"):
        super().draw(gfx)

        self.previous.draw(gfx)
        next_surface = self.next_surface(gfx)

        for i, spawn_time in enumerate(self.squares):
            life = (self.timer - spawn_time) / self.grow_duration * self.square_size

            new_border = min(self.square_size, life - self.square_size - self.delay)
            if new_border > 0:
                r = self.get_rect(i, self.square_size)
                gfx.surf.blit(next_surface, r, r)
                life = self.square_size - new_border

            if life > 0:
                black_size = min(self.square_size, life)
                pygame.draw.rect(gfx.surf, "black", self.get_rect(i, black_size))

    def get_rect(self, idx, size):
        x, y = self.to_xy(idx)
        x = (x + 0.5) * self.square_size
        y = (y + 0.5) * self.square_size
        rect = pygame.Rect(0, 0, size, size)
        rect.center = x, y
        return rect


class SquarePatternTransition(SquareSpawnTransition):

    def __init__(
        self,
        previous: State,
        next_: State,
        pattern: Callable[[int, int], int],
        square_size=32,
        delay=64,
        grow_duration=0,
    ):
        self.pattern = pattern
        super().__init__(previous, next_, square_size, delay, grow_duration)

    def spawn_squares(self) -> List[int]:
        return [self.pattern(*self.to_xy(i)) for i in range(self.square_count())]

    @classmethod
    def circle(cls, prev, next_, delay=0, speed=1, square_size=12):
        return cls(prev, next_, lambda x, y: sqrt(x * x + y * y) * speed, square_size, delay)

    @classmethod
    def random(cls, prev, next, speed=1, square_size=16, delay=0, grow_duration=0):
        """Return a transition base on a distance from a random point."""
        w = ceil(W / square_size)
        h = ceil(H / square_size)

        point = choice([(w * x, h * y) for x in (0, 0.5, 1)
                        for y in (0, 0.5, 1)] + [(uniform(0, w), uniform(0, h))])

        pattern = choice([
            lambda x, y: sqrt((x - point[0])**2 + (y - point[1])**2),  # circle
            lambda x, y: abs(x - point[0]) + abs(y - point[1]),  # diamond
            lambda x, y: max(abs(x - point[0]), abs(y - point[1])),  # square
        ])

        return cls(
            prev,
            next,
            lambda x, y: int(pattern(x, y)),
            square_size,
            delay,
            grow_duration,
        )


if __name__ == "__main__":
    # This example can be run with:
    #   python -m src.engine.state_transitions

    from random import randint
    from .utils import random_rainbow_color, random_in_rect
    from .app import App
    from .screen import FixedScreen

    class DummyState(State):
        """State with random circles, that transitions to itself with random transition."""

        BG_COLOR = 0x321254

        def __init__(self):
            super().__init__()
            self.data = [(random_in_rect(SCREEN), random_rainbow_color(70, 80), randint(4, 25))
                         for _ in range(100)]

        def draw(self, gfx: "GFX"):
            super().draw(gfx)

            for center, color, radius in self.data:
                pygame.draw.circle(gfx.surf, color, center, radius)

        def logic(self):
            super().logic()
            if self.timer > 30:
                next_ = DummyState() if isinstance(self, DummyState2) else DummyState2()
                self.replace_state(SquarePatternTransition.random(self, next_))

    class DummyState2(DummyState):
        BG_COLOR = 0x541232

    App(DummyState, FixedScreen(SIZE)).run()
