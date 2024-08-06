import itertools
import json
from bisect import bisect_left, bisect_right
from functools import lru_cache
from pathlib import Path

import pygame


ASSETS_DIR: Path | None = None


def set_assets_dir(path: Path):
    global ASSETS_DIR
    ASSETS_DIR = path


@lru_cache()
def image(name: str):
    assert ASSETS_DIR, "You need to call assets.set_assets_dir() before using images."
    file = ASSETS_DIR / "images" / (name + ".png")
    return pygame.image.load(file)


@lru_cache()
def font(name: str, size: int):
    assert ASSETS_DIR, "You need to call assets.set_assets_dir() before using fonts."
    file = ASSETS_DIR / "fonts" / (name + ".ttf")
    return pygame.font.Font(file, size)


class Animation:
    def __init__(self, name: str, flip_x=False):
        assert ASSETS_DIR, "You need to call assets.set_assets_dir() before using animations."
        self.name, self.anim = name.split()
        data = ASSETS_DIR / "animations" / (self.name + ".json")
        data = json.loads(data.read_text())
        self.timer = 0
        self.tile_sheet = data["tile_sheet"]
        self.tile_x = data["tile_x"]
        self.tile_y = data["tile_y"]
        self.line = data["anims"][self.anim]["line"]
        self.length = data["anims"][self.anim]["length"]
        dur = data["anims"][self.anim]["duration"]
        self.durations = [dur] * self.length if isinstance(dur, int) else dur
        assert len(self.durations) == self.length
        self.cum_duration = list(itertools.accumulate(self.durations))
        self.flip = data["anims"][self.anim].get("flip", False)
        self.flip_x = flip_x

    def __len__(self):
        """Number of frames for one full loop."""
        if self.flip:
            return self.cum_duration[-1] + self.cum_duration[-2]
        return self.cum_duration[-1]

    def update(self):
        self.timer += 1

    def image(self):
        time = self.timer % len(self)
        if self.flip and time >= self.cum_duration[-1]:
            time = self.cum_duration[-1] + self.cum_duration[-2] - time - 1
        # Find the index where the time should go
        frame = bisect_right(self.cum_duration, time)

        return self._image(
            self.tile_sheet, frame, self.line, self.tile_x, self.tile_y, self.flip_x
        )

    @staticmethod
    @lru_cache()
    def _image(sheet: str, x, y, tx, ty, flip_x):
        surf = image(sheet)
        img = surf.subsurface(tx * x, ty * y, tx, ty)
        return pygame.transform.flip(img, flip_x, False)
