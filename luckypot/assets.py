import itertools
import json
from bisect import bisect_left, bisect_right
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pygame

from .constants import *
from .settings import settings
from .utils import overlay


__all__ = [
    "set_assets_dir",
    "sound",
    "play",
    "image",
    "rotate",
    "scale",
    "font",
    "text",
    "colored_text",
    "wrapped_text",
    "tilemap",
    "Image",
    "SpriteSheet",
    "Assets",
    "Animation",
    "AnimationV2",
]


ASSETS_DIR: Path | None = None
SFX = "sfx"
IMAGES = "images"
ANIMATIONS = "animations"
FONTS = "fonts"
MUSIC = "music"


def set_assets_dir(path: Path):
    """Set the path to the assets directory. This needs to be called before using any asset."""
    global ASSETS_DIR
    ASSETS_DIR = path

@lru_cache()
def sound(name):
    assert ASSETS_DIR, "You need to call assets.set_assets_dir() before."
    file = ASSETS_DIR / SFX / (name + ".wav")
    sound = pygame.mixer.Sound(file)

    sound.set_volume(VOLUMES.get(name, 1.0) * 0.1)

    return sound


def play(name: str):
    if not settings.mute:
        s = sound(name)
        s.stop()
        s.play()


@lru_cache()
def image(name: str):
    assert ASSETS_DIR, "You need to call assets.set_assets_dir() before."
    file = ASSETS_DIR / IMAGES / (name + ".png")
    print(f"Load {file}")
    img = pygame.image.load(file)

    if name.startswith("planet"):
        return overlay(img, (0, 0, 0, 100))
    return img


@lru_cache(10000)
def rotate(image, degrees):
    return pygame.transform.rotate(image, degrees)


@lru_cache(1000)
def scale(image, factor):
    if not isinstance(factor, int):
        print(f"Warning: scaling {image} by non integer factor {factor}.")
    size = int(factor * image.get_width()), int(factor * image.get_height())
    return pygame.transform.scale(image, size)


@lru_cache()
def font(size: int, name: str | None = None):
    assert ASSETS_DIR, "You need to call assets.set_assets_dir() before."
    name = name or BIG_FONT
    file = ASSETS_DIR / FONTS / (name + ".ttf")
    return pygame.font.Font(file, size)


@lru_cache(10000)
def text(txt, size, color, font_name=None):
    antialias = ANTIALIASING_ALIAS.get(font_name or BIG_FONT, True)
    return font(size, font_name).render(txt, antialias, color)


@lru_cache(1000)
def colored_text(size, *parts, name=None):
    surfaces = []
    for txt, color in parts:
        s = text(txt, size, color, name)
        surfaces.append(s)

    w = sum(s.get_width() for s in surfaces)
    h = max(s.get_height() for s in surfaces)
    output = pygame.Surface((w, h))
    output.set_colorkey((0, 0, 0))

    x = 0
    for surf in surfaces:
        output.blit(surf, (x, 0))
        x += surf.get_width()

    return output


@lru_cache()
def wrapped_text(txt: str, size, color, max_width, name=None, align_right=False) -> pygame.Surface:
    f = font(size, name)

    words = txt.split()
    surfaces = []
    while words:
        line = []
        while f.size(" ".join(line))[0] < max_width:
            if not words:
                break
            line.append(words.pop(0))
        else:
            words.insert(0, line.pop())
        surfaces.append(text(" ".join(line), size, color, name))

    w = max(s.get_width() for s in surfaces)
    h = sum(s.get_height() for s in surfaces)

    output = pygame.Surface((w, h), pygame.SRCALPHA)
    output.fill((0, 0, 0, 0))

    y = 0
    for surf in surfaces:
        if align_right:
            output.blit(surf, surf.get_rect(topright=(w, y)))
        else:
            output.blit(surf, surf.get_rect(midtop=(w / 2, y)))
        y += surf.get_height()

    return output


@lru_cache()
def tilemap(name, x, y, tile_size=32):
    img = image(name)
    w = img.get_width()

    # Wrap x when bigger than line length
    tiles_in_a_row = w // tile_size
    y += x // tiles_in_a_row
    x %= tiles_in_a_row

    return img.subsurface((x * tile_size, y * tile_size, tile_size, tile_size))


class Image:

    def __init__(self, name):
        self.name = name
        self.surface: Optional[pygame.Surface] = None

    def load(self):
        """Load the image from disk if needed."""
        if self.surface is None:
            self.surface = image(self.name)

    def __call__(self, *args, **kwargs):
        self.load()
        return self.surface


class SpriteSheet(Image):

    def __init__(self, name, tile_size, auto_crop=False):
        super().__init__(name)
        self.tile_size = tile_size

    def __call__(self, col, row=0):
        """Return the image at the (col, row) position on the spritesheet"""

        self.load()

        # Wrap column when bigger than line length
        tiles_in_a_row = self.surface.get_width() // self.tile_size
        row += col // tiles_in_a_row
        col %= tiles_in_a_row

        return self.surface.subsurface(
            (col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size))


class Assets:

    class Images:
        enemies = SpriteSheet("enemies", 16)
        player = Image("player")
        cards = SpriteSheet("sprite", 16)

    class Sounds:
        pass

    class Transform:
        pass

    def __init__(self):
        raise RuntimeError("The Assets class is just a namespace and not meant to be instanciated.")


# We can do better...


class AnimationV2:

    def __init__(self, name: str, override_frame_duration=None, flip_x=False):
        self.timer = 0
        self.name = name

        assert ASSETS_DIR, "You need to call assets.set_assets_dir() before."
        data = ASSETS_DIR / ANIMATIONS / (self.name + ".json")
        data = json.loads(data.read_text())

        self.tile_size = data["tile_size"]
        self.frame_nb = data["length"]
        self.frame_duration = override_frame_duration or data["duration"]
        self.flip_x = flip_x

    def __len__(self):
        """Number of frames for one full loop."""
        return self.frame_nb * self.frame_duration

    def logic(self):
        self.timer += 1

    def image(self):
        time = self.timer % len(self)
        frame_nb = time // self.frame_duration
        return tilemap(self.name, frame_nb, 0, self.tile_size)


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
