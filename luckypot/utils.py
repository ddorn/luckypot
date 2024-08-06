from __future__ import annotations

import bisect
import contextlib
import functools
import math
import random
import typing
from functools import lru_cache

import pygame

if typing.TYPE_CHECKING:
    from pygame._common import ColorValue


def vec2int(vec):
    """Convert a 2D vector to a tuple of integers."""
    return int(vec[0]), int(vec[1])


@lru_cache()
def load_img(path, alpha=False):
    if alpha:
        return pygame.image.load(path).convert_alpha()
    return pygame.image.load(path)


@lru_cache()
def get_tile(tilesheet: pygame.Surface, size, x, y, w=1, h=1):
    return tilesheet.subsurface(x * size, y * size, w * size, h * size)


def lerp(a, b, t, clamp: bool = False):
    """Linear interpolation between a and b. Return a when t=0 and b when t=1."""
    if clamp:
        t = min(1, max(0, t))
    return (1 - t) * a + t * b


def lerp_multi(t: float, *points: tuple[float, float]) -> float:
    """
    Linear interpolation between multiple points. Return the first point when t=0 and the last point when t=1.

    Args:
        t: The interpolation factor.
        points: The points to interpolate between. Must be sorted by time.
            Each point is a tuple (x, y) where x is the time and y is the value at that time.
    """
    for (t1, y1), (t2, y2) in zip(points, points[1:]):
        if t1 <= t <= t2:
            # We inline everything for perfs (no call to chrange)
            prop = (t - t1) / (t2 - t1)
            return (1 - prop) * y1 + prop * y2

    # This check is after the for loop, as it is the least likely to happen.
    # When this function is called in particles update, we want the fastest path
    # to be the one above
    if t <= 0:
        return points[0][1]
    if t >= 1:
        return points[-1][1]
    if len(points) == 1:
        return points[0][1]

    # Should never happen.
    # Are points not sorted? -> raise an error
    for (t1, y1), (t2, y2) in zip(points, points[1:]):
        if t1 > t2:
            raise ValueError(f"Points are not sorted: {points}")
    raise ValueError(f"Uh? t={t}, points={points}")


def mix(color1, color2, t):
    """Mix two colors. Return color1 when t=0 and color2 when t=1."""

    return (
        round((1 - t) * color1[0] + t * color2[0]),
        round((1 - t) * color1[1] + t * color2[1]),
        round((1 - t) * color1[2] + t * color2[2]),
    )


def chrange(
    x: float,
    initial_range: tuple[float, float],
    target_range: tuple[float, float],
    power=1,
    flipped=False,
    clamp=False,
):
    """Change the range of a number by mapping the initial_range to target_range using a linear transformation."""
    normalised = (x - initial_range[0]) / (initial_range[1] - initial_range[0])
    if flipped:
        normalised = 1 - normalised
    if clamp:
        normalised = min(1.0, max(0.0, normalised))

    normalised **= power
    return normalised * (target_range[1] - target_range[0]) + target_range[0]


def rrange(nb: float):
    """Return a range with a length of `nb` in expectation."""
    qte = int(nb)
    proba = nb - qte
    if random.random() < proba:
        return range(qte + 1)
    return range(qte)


def from_polar(r: float, angle: float):
    """Create a vector with the given polar coordinates. angle is in degrees."""
    vec = pygame.Vector2()
    vec.from_polar((r, angle))
    return vec


def clamp(x: float, mini: float, maxi: float):
    """Clamp a number between mini and maxi."""
    if x < mini:
        return mini
    if x > maxi:
        return maxi
    return x


def smoothstep(x, x_min: float = 0, x_max: float = 1, n: int = 1):
    """
    Smoothstep function. See https://en.wikipedia.org/wiki/Smoothstep.

    Args:
        x: The value to interpolate.
        x_min: The minimum value that the function can take.
        x_max: The maximum value that the function can take.
        n: The degree of the polynomial used to interpolate.

    Returns:
        A value between 0 and 1.
    """

    x = clamp((x - x_min) / (x_max - x_min), 0, 1)

    result = 0
    for k in range(0, n + 1):
        result += math.comb(k + n, k) * math.comb(2 * n + 1, n - k) * (-x)**k

    result *= x**(n + 1)

    return result


def soft_clamp(x, mini: float, maxi: float, smooth_size: float):
    """Clamp a number between mini and maxi, but in a smooth way.

    Outside the ranges mini ± smooth_size and maxi ± smooth_size, the function
    takes the same value as clamp. Between these ranges, the function has a
    continuous derivative.

    What I want for the interpolation part:
    - f(-1) = 0
    - f(1) = 1
    - f'(-1) = 0
    - f'(1) = 1

    f(x) = ax^3 + bx^2 + cx + d
    f'(x) = 3ax^2 + 2bx + c
    The system is:
    -a + b - c + d = 0
    a + b + c + d = 1
    3a - 2b + c = 0
    3a + 2b + c = 1
    The solution is:
    a = 0; b = 1/4; c = 1/2; d = 1/4

    So:
    f(x) = 1/4 * x^2 + 1/2 * x + 1/4
    """

    def f(x):
        return x**2 / 4 + x / 2 + 1 / 4

    ss = smooth_size / 2

    if x < mini - ss:
        return mini
    elif x < mini + ss:
        prop = chrange(x, (mini - ss, mini + ss), (-1, 1))
        return mini + smooth_size * f(prop) / 2
    elif x < maxi - ss:
        return x
    elif x < maxi + ss:
        prop = chrange(x, (maxi - ss, maxi + ss), (-1, 1))
        return maxi - smooth_size * f(-prop) / 2
    else:
        return maxi


def angle_towards(start, goal, max_movement):
    """Return the angle towards goal that is a most max_movement degrees from the start angle."""
    start %= 360
    goal %= 360

    if abs(start - goal) > 180:
        return start + clamp(start - goal, -max_movement, max_movement)
    else:
        return start + clamp(goal - start, -max_movement, max_movement)


def random_in_rect(rect: pygame.Rect, x_range=(0.0, 1.0), y_range=(0.0, 1.0)):
    """Return a random point inside a rectangle.

    If x_range or y_range are given, they are interpreted as relative to the size of the rectangle.
    For instance, a x_range of (-1, 3) would make the x range in a rectangle that is 3 times wider,
    but still centered at the same position. (-2, 1) you expand the rectangle twice its size on the
    left.
    """
    w, h = rect.size

    return (
        random.uniform(rect.x + w * x_range[0], rect.x + w * x_range[1]),
        random.uniform(rect.y + h * y_range[0], rect.y + h * y_range[1]),
    )


def random_in_surface(surf: pygame.Surface, max_retries=100):
    """Return a random point that is not transparent in a surface.

    After max_retry, returns the center of the surface.
    """
    w, h = surf.get_size()
    color_key = surf.get_colorkey()
    with lock(surf):
        for _ in range(max_retries):
            pos = random.randrange(w), random.randrange(h)
            color = surf.get_at(pos)
            if not (color == color_key or color[3] == 0):
                # Pixel is not transparent.
                return pos
        return w // 2, h // 2


@contextlib.contextmanager
def lock(surf):
    """A simple context manager to automatically lock and unlock the surface."""
    surf.lock()
    try:
        yield
    finally:
        surf.unlock()


def clamp_length(vec, maxi):
    """Scale the vector so it has a length of at most :maxi:"""

    if vec.length() > maxi:
        vec.scale_to_length(maxi)

    return vec


def part_perp_to(u, v):
    """Return the part of u that is perpendicular to v"""
    if v.length_squared() == 0:
        return u

    v = v.normalize()
    return u - v * v.dot(u)


def prop_in_rect(rect: pygame.Rect, prop_x: float, prop_y: float):
    """Return the point in a rectangle defined by the proportion.

    Examples:
        (0, 0) => topleft
        (1/3, 1/3) => point at the first third of the rect
        (-1, 0) => point on the top-line and one width on the leftj
    """

    return rect.x + rect.w * prop_x, rect.y + rect.h * prop_y


def bounce(x, f=0.2, k=60):
    """Easing function that bonces over 1 and then stabilises around 1.

    Graph:
         │   /^\
        1│  /   `------
        0│ /
         ┼———————————————
           0 f        1

    Args:
        x: The time to animate, usually between 0 and 1, but can be greater than one.
        f: Time to grow to 1
        k: Strength of the bump after it has reached 1
    """

    s = max(x - f, 0.0)
    return min(x * x / (f * f), 1 + (2.0 / f) * s * math.exp(-k * s))


def exp_impulse(x, k):
    """
    Easing function that rises quickly to one and slowly goes back to 0.

    Graph:
        1│   /^\
         │  /    \
        0│ /      `-_
         ┼————┼——————————
           0  │    1
              ╰ 1/k

    Args:
        x: The time to animate, usually between 0 and 1, but can be greater than one.
        k: Control the stretching of the function

    Returns: a float between 0 and 1.
    """

    h = k * x
    return h * math.exp(1.0 - h)


def exp_impulse_integral(k):
    """
    Value of the integral of exp_impulse between 0 and 1.

    Can be used to determine the total change in position
    if exp_impulse is used to change a velocity.
    """

    return math.exp(1 - k) * (-k + math.exp(k) - 1) / k


def soft_plus(x: float, k: float = 1.0):
    """
    A smooth approximation of the ReLU function.

    Graph:
        1│       /
         │     /
        0│__-'
         ┼———┼-——————————
         0  │    1
            ╰ 0

    Args:
        x: Input value
        k: Controls the smoothness of the function, the higher the sharper.
    """

    if x * k > 40:
        # Avoid overflow, it's only the identity function in this range anyway.
        return x
    return math.log(1 + math.exp(k * x)) / k


def auto_crop(surf: pygame.Surface):
    """Return the smallest subsurface of an image that contains all the visible pixels."""

    rect = surf.get_bounding_rect()
    return surf.subsurface(rect)


def outline(surf: pygame.Surface, color=(255, 255, 255)):
    """Create an outline on the surface of the given color."""

    mask = pygame.mask.from_surface(surf)
    outline_points = mask.outline()
    output = pygame.Surface((surf.get_width() + 2, surf.get_height() + 2))

    with lock(output):
        for x, y in outline_points:
            for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                output.set_at((x + dx + 1, y + dy + 1), color)

    output.blit(surf, (1, 1))

    output.set_colorkey(surf.get_colorkey())

    return output


@functools.lru_cache(1000)
def overlay(image: pygame.Surface, color, alpha=255):
    img = pygame.Surface(image.get_size())
    img.fill(1)  # 1 is a color unlikely to be used (hopefully)
    img.set_colorkey(1)
    img.blit(image, (0, 0))

    mask = pygame.mask.from_surface(image)
    overlay = mask.to_surface(setcolor=color, unsetcolor=(255, 255, 0, 0))
    overlay.set_alpha(alpha)
    img.blit(overlay, (0, 0))

    return img


def random_in_rect_and_avoid(
    rect: pygame.Rect,
    avoid_positions,
    avoid_radius,
    max_trials=1000,
    force_y=None,
    default=None,
):
    for trial in range(max_trials):
        if force_y is not None:
            pos = random.uniform(rect.left, rect.right), force_y
        else:
            pos = random_in_rect(rect)

        # Any position is too close
        for p in avoid_positions:
            if p.distance_to(pos) < avoid_radius:
                break
        else:
            return pos

    return default


def random_rainbow_color(saturation=100, value=100):
    """Get a random color from the rainbow.

    Args:
        saturation: integer between 0 and 100
        value: integer between 0 and 100
    """
    hue = random.randrange(0, 360)
    color = pygame.Color(0)
    color.hsva = hue, saturation, value, 100
    return color


def from_hsv(hue, saturation, value, alpha=100):
    """
    Create a color from HSV values.

    Args:
        hue: The hue of the color, between 0 and 360
        saturation: The saturation of the color, between 0 and 100. Out of range values are clamped.
        value: The value of the color, between 0 and 100. Out of range values are clamped.
        alpha: The alpha of the color, between 0 and 100. Out of range values are clamped.
    """

    hue = hue % 360
    saturation = max(0, min(100, saturation))
    value = max(0, min(100, value))
    alpha = max(0, min(100, alpha))

    color = pygame.Color(0)
    color.hsva = hue, saturation, value, alpha
    return color


def gradient(t: float, *color_spec: tuple[float, ColorValue]) -> pygame.Color:
    """
    Return a color that is a linear interpolation between the colors.

    Args:
        t: The position of the color to return
        *color_spec: A list of (position, color) pairs. When t is between two positions, the color is interpolated.
    """
    assert color_spec, "At least one color must be specified"

    # Sort the colors by position
    color_spec = sorted(color_spec, key=lambda x: x[0])

    if t <= color_spec[0][0]:
        return pygame.Color(color_spec[0][1])
    if t >= color_spec[-1][0]:
        return pygame.Color(color_spec[-1][1])

    # Find the two colors to interpolate between
    pos = bisect.bisect(color_spec, t, key=lambda x: x[0])
    pos1, color1 = color_spec[pos - 1]
    pos2, color2 = color_spec[pos]

    # Interpolate
    t = (t - pos1) / (pos2 - pos1)
    return pygame.Color(color1).lerp(color2, t)


class Cooldown:

    def __init__(self, duration: float):
        self.auto_lock = duration
        self.locked_for = 0

    def lock_for(self, duration):
        """Lock the cooldown for duration. If already locked, increases the duration of the lock."""
        self.locked_for = min(duration, self.locked_for + duration)

    def tick(self, fire=False, override_duration: float = None) -> bool:
        """Advance the cooldown and when fire is True, return whether the cooldown is over.

        If the cooldown is over and fire is True, restart the cooldown.
        """

        self.locked_for -= 1
        if fire and self.locked_for <= 0:
            self.locked_for = override_duration or self.auto_lock
            return True
        return False

    def fire(self) -> bool:
        """Whether the cooldown is over. Reset the cooldown if needed."""
        if self.locked_for <= 0:
            self.locked_for = self.auto_lock
            return True
        return False


__all__ = [
    "vec2int",
    "load_img",
    "get_tile",
    "lerp",
    "lerp_multi",
    "mix",
    "chrange",
    "rrange",
    "from_polar",
    "clamp",
    "smoothstep",
    "soft_clamp",
    "angle_towards",
    "random_in_rect",
    "random_in_surface",
    "lock",
    "clamp_length",
    "part_perp_to",
    "prop_in_rect",
    "bounce",
    "exp_impulse",
    "exp_impulse_integral",
    "soft_plus",
    "auto_crop",
    "outline",
    "overlay",
    "random_in_rect_and_avoid",
    "random_rainbow_color",
    "from_hsv",
    "gradient",
    "Cooldown",
]

# This just helps me to remember to add new utilities to __all__
IGNORE = [lru_cache]
for name, f in list(globals().items()):
    if name not in __all__ and callable(f) and f not in IGNORE:
        raise RuntimeError(f"{name} is not exported, did you forget to add it to __all__?")
