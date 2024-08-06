from __future__ import annotations

from math import cos, pi, sin
from random import choice, gauss, randint, uniform
from time import time
from typing import Callable, Generic, Optional, Tuple, TypeVar, Union, Self

import pygame
import pygame.gfxdraw
from pygame import Vector2, Rect

#
__all__ = [
    "ParticleSystem",
    "ParticleFountain",
    "Particle",
    "DrawnParticle",
    "PolygonParticle",
    "ImageParticle",
    "CircleParticle",
    "LineParticle",
    "SquareParticle",
    "ShardParticle",
    "TextParticle",
    "rrange",
]

from .assets import text
from .utils import bounce, exp_impulse, random_in_rect, random_in_rect_and_avoid, rrange, clamp, from_polar
from .gfx import GFX


DEGREES = float
VEC2D = Union[Tuple[float, float], Vector2]
P = TypeVar("P", bound="Particle")

radians = pi / 180

SNOW = pygame.image.fromstring(
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00\x00\x00\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00\x00\x001\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf2\x00\x00\x001\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x841\xa2\xf2\x00W\x841\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00W\x841\xa2\xf2\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x84\x00\x00\x00\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x841\xa2\xf2\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf2\x00\x00\x001\xa2\xf2\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x841\xa2\xf2\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf21\xa2\xf2\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x84\x00W\x84\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x001\xa2\xf21\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00\x00\x00\x00W\x84\x00\x00\x001\xa2\xf2\x00\x00\x00\x00W\x84\x00\x00\x00\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00\x00\x001\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00\x00\x00\x00W\x84\x00\x00\x001\xa2\xf2\x00\x00\x00\x00W\x84\x00\x00\x00\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf21\xa2\xf2\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x84\x00W\x84\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x001\xa2\xf21\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf2\x00\x00\x001\xa2\xf2\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x841\xa2\xf2\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x84\x00\x00\x00\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x841\xa2\xf2\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x841\xa2\xf2\x00W\x841\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00W\x841\xa2\xf2\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00\x00\x001\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00\x00\x00\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf21\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x841\xa2\xf2\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00W\x84\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    (24, 24),
    "RGB",
)


def vec2int(vec):
    return (int(vec[0]), int(vec[1]))


def rand2d(vec):
    return uniform(0, vec[0]), uniform(0, vec[1])


class ParticleSystem(set):
    fountains: "list[ParticleFountain]"

    def __init__(self):
        super().__init__()
        self.fountains = []
        self.use_gfx = True  # Change to False for slightly better performance

    def logic(self):
        """Update all the particle for the frame."""

        for fountain in self.fountains:
            fountain.logic(self)

        dead = set()
        for particle in self:
            particle.logic()
            if not particle.alive:
                dead.add(particle)

        self.difference_update(dead)

    def draw(self, gfx: GFX):
        """Draw all the particles"""

        if self.use_gfx:
            for particle in self:
                particle.draw(gfx)
        else:
            for particle in self:
                particle.draw_no_gfx(gfx.surf)

    def add_fire_particle(self, pos, angle):
        self.add(
            SquareParticle()
            .builder()
            .hsv(gauss(20, 20), gauss(100, 10))
            .at(pos, gauss(angle, 10))
            .velocity(gauss(1, 0.1))
            .sized(uniform(1, 5))
            .living(30)
            .anim_fade()
            .build()
        )

    def add_explosion(self, pos, intensity=100, qte: Optional[float] = None, color="white"):
        if qte is None:
            qte = intensity / 2

        for i in rrange(qte):
            self.add(
                SquareParticle(color)
                .builder()
                .at(pos, uniform(0, 360))
                .velocity(gauss(intensity / 30, intensity / 100))
                .sized(2)
                .living(intensity // 4)
                .anim_fade()
                .build()
            )


class ParticleFountain:
    def __init__(
            self, particle_generator: Callable[[], "Particle"], frequency=1.0,
    ):
        self.generator = particle_generator
        self.frequency = frequency

    def logic(self, system):
        for _ in rrange(self.frequency):
            system.add(self.generator())

    @classmethod
    def stars(cls, rect):
        """Spawn stars particles in the rectangle."""
        return cls(
            lambda: SquareParticle("white")
            .builder()
            .at(random_in_rect(rect), 90)
            .velocity(0.2)
            .living(6 * 60)
            .sized(uniform(1, 3))
            .anim_blink()
            .build(),
            0.2,
        )

    @classmethod
    def screen_confetti(cls, rect: Rect, n_sources: int = 10):
        """Spawn confetti covering the screen from n_sources positions."""
        positions = []
        for _ in range(n_sources):
            positions.append(
                Vector2(random_in_rect_and_avoid(rect, positions, 80))
            )

        return cls(
            lambda: CircleParticle()
            .builder()
            .hsv(angle := uniform(0, 360), 80, 80)
            .at(choice(positions) + from_polar(40, angle), angle + 90)
            .velocity(gauss(2, 0.2), )
            .sized(gauss(5, 2))
            # .acceleration(-0.005)
            .living(400)
            .build(), frequency=n_sources)


class Particle:
    def __init__(self):
        self.pos = Vector2(0, 0)
        self.speed = 3.0
        self.angle = -90
        self.acc = 0.0
        self.angle_vel = 0.0
        self.size = 10.0
        self.lifespan = 60
        self.constant_force = Vector2()

        self.inner_rotation = 0
        self.inner_rotation_speed = 0
        self.alpha = 255

        self.life_prop = 0.0
        self.alive = True
        self.animations = []

    # Builder methods

    class Builder(Generic[P]):
        def __init__(self, particle: P):
            self._p: P = particle

        def at(self, pos: VEC2D, angle: DEGREES = 0):
            """
            Set the initial conditions.

            Args:
                pos: 2D position in pixels
                angle: initial target in degrees

            Returns:
                The particle being build.
            """

            self._p.pos = Vector2(pos)
            self._p.angle = angle
            return self

        def velocity(self, speed: float, radial_velocity: DEGREES = 0):
            """Speed is along the target, and radial_velocity is how fast this target changes.

            Args:
                speed: px/frame along the target
                radial_velocity: degrees/frame of angle change
            """
            self._p.speed = speed
            self._p.angle_vel = radial_velocity
            return self

        def constant_force(self, velocity: Vector2):
            """Add the given velocity to the particle's position every frame."""

            self._p.constant_force = velocity
            return self

        def acceleration(self, directional: float):
            """Set the acceleration along the target and the angular acceleration"""
            self._p.acc = directional
            return self

        def inner_rotation(self, start: DEGREES, speed: DEGREES):
            """Set the rotation of the particle. This does not affect its motion."""
            self._p.inner_rotation = start
            self._p.inner_rotation_speed = speed
            return self

        def sized(self, size: float):
            """Set the radius of the particle."""
            self._p.size = size
            return self

        def living(self, lifespan: int):
            """Set how many frames the particle will be alive."""
            self._p.lifespan = lifespan
            return self

        def transparency(self, alpha: int):
            """Set the transparency of the particle between 0 and 255."""
            self._p.alpha = alpha
            return self

        def anim(self, animation: Callable[[P], None]) -> Self:
            self._p.animations.append(animation)
            return self

        def anim_attr(self, attr: str, func: Callable[[float], float]) -> Self:
            """Set the attribute of the particle using a function of its life proportion."""
            assert hasattr(self._p, attr), f"Particle has no attribute {attr}"

            def anim(particle: P):
                setattr(particle, attr, func(particle.life_prop))
            return self.anim(anim)

        def anim_alpha(self, func: Callable[[float], int]) -> Self:
            """Set the alpha of the particle using a function of its life proportion."""
            def anim(particle: P):
                particle.alpha = func(particle.life_prop)
            return self.anim(anim)

        def anim_fade(self, fade_start=0):
            def fade(particle: P, fs=fade_start):
                if particle.life_prop > fs:
                    t = (particle.life_prop - fs) / (1 - fs)
                    particle.alpha = int(255 * (1 - t))

            return self.anim(fade)

        def anim_gravity(self, gravity: float | Vector2 | tuple[float, float]) -> Self:
            """Add gravity to the particle."""
            if isinstance(gravity, (int, float)):
                gravity = Vector2(0, gravity)

            def gravity_anim(particle: Particle):
                vel = from_polar(particle.speed, particle.angle)
                vel += gravity
                particle.speed, particle.angle = vel.as_polar()

            return self.anim(gravity_anim)

        def anim_blink(self, up_duration=0.5, pow=2):
            """Make the particle blink.
            Increase alpha linearly for a proportion of `up_duration` of its life, then decrease it linearly.
            If `pow` is not 1, uses a power function instead of a linear one.
            """
            def blink(particle):
                if particle.life_prop < up_duration:
                    a = particle.life_prop / up_duration
                else:
                    a = (1 - particle.life_prop) / (1 - up_duration)
                # a = 1 - abs(1 - 2 * particle.life_prop)
                particle.alpha = int(255 * a ** pow)

            return self.anim(blink)

        def anim_bounce_rect(self, rect):
            """Make the particle bounce on the sides, inside the rectangle."""

            rect = pygame.Rect(rect)

            def bounce_rect(particle):
                angle = particle.angle % 360
                if particle.pos.x - particle.size < rect.left and 90 < angle < 270:
                    particle.angle = 180 - angle
                elif particle.pos.x + particle.size > rect.right and (angle < 90 or angle > 270):
                    particle.angle = 180 - angle

                angle = particle.angle % 360
                if particle.pos.y - particle.size < rect.top and angle > 180:
                    particle.angle = -angle
                elif particle.pos.y + particle.size > rect.bottom and angle < 180:
                    particle.angle = -angle

            return self.anim(bounce_rect)

        def anim_shrink(self):
            """Make the particle shrink linearly as it ages."""
            initial_size = self._p.size

            def shrink(particle):
                particle.size = initial_size * (1 - particle.life_prop)

            return self.anim(shrink)

        def anim_bounce_size(self, increase_duration=0.3, k=10):
            initial_size = self._p.size

            def bounce_size(particle):
                particle.size = bounce(particle.life_prop, increase_duration, k) * initial_size

            return self.anim(bounce_size)

        def anim_bounce_size_and_shrink(self, stretch=5):
            initial_size = self._p.size

            def bounce_size_and_shrink(particle):
                particle.size = exp_impulse(particle.life_prop, stretch) * initial_size

            return self.anim(bounce_size_and_shrink)

        def apply(self, func):
            """Call a building function on the particle. Useful to factor parts of the build."""
            func(self)
            return self

        def build(self) -> P:
            return self._p

    def builder(self):
        return self.Builder(self)

    # Actual methods

    def logic(self):
        """Update the attributes of the particle."""

        self.life_prop += 1 / self.lifespan
        self.speed += self.acc
        self.angle += self.angle_vel
        self.pos += (
            cos(self.angle * radians) * self.speed,
            sin(self.angle * radians) * self.speed,
        )
        self.pos += self.constant_force

        self.inner_rotation += self.inner_rotation_speed

        if self.speed < 0 or self.size <= 0 or self.life_prop >= 1:
            self.alive = False
        else:
            for anim in self.animations:
                anim(self)

    def draw(self, gfx: GFX):
        raise NotImplementedError(f"Particle {self} does not implement draw()")

    def draw_no_gfx(self, screen):
        raise NotImplementedError(f"Particle {self} does not implement draw_no_gfx()")


class DrawnParticle(Particle):
    def __init__(self, color=None):
        self.color = pygame.Color(color or 0)
        Particle.__init__(self)

    @property
    def alpha(self):
        return self.color.a

    @alpha.setter
    def alpha(self, value: int):
        self.color.a = value

    class Builder(Particle.Builder["DrawnParticle"]):
        def hsv(self, hue: float, saturation: float = 100, value: float = 100):
            hue = round(hue) % 360
            saturation = clamp(saturation, 0, 100)
            value = clamp(value, 0, 100)
            self._p.color.hsva = (hue, saturation, value, 100)
            return self

        def anim_gradient_to(self, h0, s0, v0, h1, v1, s1):
            """Animate the color of the particle in hsv space.

            Animations of the transparency should come after this one
            """

            # h0, s0, v0, a = self._p.color.hsva
            # h1 = h if h is not None else h0
            # s1 = clamp(s) * 100 if s is not None else s0
            # v1 = clamp(v) * 100 if v is not None else v0

            def gradient_to(particle):
                p = 1 - particle.life_prop
                t = particle.life_prop

                h = int(p * h0 + t * h1) % 360
                s = int(100 * (p * s0 + t * s1))
                v = int(100 * (p * v0 + t * v1))
                r = h, s, v, 100
                particle.color.hsva = r

            return self.anim(gradient_to)

    def builder(self) -> Builder:
        # the method is here only for type hinting
        return self.Builder(self)


class CircleParticle(DrawnParticle):
    def __init__(self, color=None, filled=True):
        super().__init__(color)
        self.filled = filled

    def draw(self, gfx: GFX):
        gfx.circle(self.color, self.pos, self.size, 1 - self.filled)

    def draw_no_gfx(self, surf):
        if self.color.a < 255:
            if self.filled:
                pygame.gfxdraw.filled_circle(
                    surf, int(self.pos.x), int(self.pos.y), int(self.size), self.color
                )
            else:
                pygame.gfxdraw.circle(surf, int(self.pos.x), int(self.pos.y), int(self.size), self.color)

        else:
            pygame.draw.circle(surf, self.color, self.pos, self.size, 1 - self.filled)


class SquareParticle(DrawnParticle):
    def draw(self, gfx: GFX):
        gfx.box(self.color, (self.pos - (self.size / 2, self.size / 2), (self.size, self.size)))

    def draw_no_gfx(self, surf):
        pos = self.pos - (self.size / 2, self.size / 2)
        if self.color.a < 255:
            pygame.gfxdraw.box(surf, (pos, (self.size, self.size)), self.color)
        else:
            pygame.draw.rect(surf, self.color, (pos, (self.size, self.size)))


class PolygonParticle(DrawnParticle):
    def __init__(self, vertices: int, color=None, vertex_step: int = 1):
        """
        A particle shaped in a regular polygon.

        Args:
            vertices: number of vertices
            color:
            vertex_step: order in which to draw the vertices.
                This can be used to draw star shaped pattern.
                Rhe order will be 1, 1+step, 1+2*step...
                should be coprime with vertices.
        """

        super().__init__(color)
        self.vertex_step = vertex_step
        self.vertices = vertices

    def draw(self, gfx: GFX):
        points = [
            self.pos
            + from_polar(self.size, self.inner_rotation + i * 360 / self.vertices * self.vertex_step, )
            for i in range(self.vertices)
        ]

        gfx.polygon(self.color, points)

    def draw_no_gfx(self, surf):
        points = [
            self.pos
            + from_polar(self.size, self.inner_rotation + i * 360 / self.vertices * self.vertex_step, )
            for i in range(self.vertices)
        ]

        pygame.gfxdraw.filled_polygon(surf, points, self.color)


class ShardParticle(DrawnParticle):
    def __init__(self, color=None, head=1, tail=3):
        """A shard shaped particle, inspired from DaFluffyPtato.

        The size of lateral size is given by the particle's size,
        and :head: and :tail: are the length of the head and tail
        compared to the side.
        """

        super().__init__(color)
        self.tail = tail
        self.head = head

    def points(self):
        vel = from_polar(self.speed, self.angle)
        vel.scale_to_length(self.size)
        cross = Vector2(-vel.y, vel.x)

        return [
            self.pos + vel * self.head,
            self.pos + cross,
            self.pos - vel * self.tail,
            self.pos - cross,
        ]

    def draw(self, gfx: GFX):
        gfx.polygon(self.color, self.points())

    def draw_no_gfx(self, surf):
        pygame.gfxdraw.filled_polygon(surf, self.points(), self.color)


class LineParticle(DrawnParticle):
    def __init__(self, length, color=None, width=1):
        self.length = length
        self.width = width
        super().__init__(color)

    def draw(self, gfx: GFX):
        end = self.pos - from_polar(self.length, self.angle)
        gfx.line(self.color, self.pos, end)

    def draw_no_gfx(self, surf):
        end = vec2int(self.pos - from_polar(self.length, self.angle))
        start = vec2int(self.pos)
        # noinspection PyTypeChecker
        pygame.gfxdraw.line(surf, *start, *end, self.color)


class ImageParticle(Particle):
    def __init__(self, surf: pygame.Surface):
        self._alpha = 255
        self.original_surf = surf
        self.need_redraw = True
        self.surf = pygame.Surface((1, 1))

        super().__init__()

        self.size = min(self.original_surf.get_size())

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value: int):
        self._alpha = value
        self.surf.set_alpha(value)

    def redraw(self):
        self.need_redraw = False
        w, h = self.original_surf.get_size()
        ratio = self.size / min(w, h)
        surf = pygame.transform.scale(self.original_surf, vec2int((w * ratio, h * ratio)))

        surf.set_alpha(self.alpha)
        return surf

    def draw(self, gfx: GFX):
        if self.need_redraw:
            self.surf = self.redraw()

        gfx.blit(self.surf, center=self.pos)

    def draw_no_gfx(self, surf: pygame.Surface):
        if self.need_redraw:
            self.surf = self.redraw()

        surf.blit(self.surf, self.surf.get_rect(center=self.pos))

    def logic(self):
        last_size = self.size
        super(ImageParticle, self).logic()
        if int(last_size) != int(self.size):
            self.need_redraw = True


class TextParticle(DrawnParticle, ImageParticle):
    def __init__(self, txt, color=None, font_name=None):
        DrawnParticle.__init__(self, color)
        self.text = txt
        self.font_name = font_name
        ImageParticle.__init__(self, self.redraw())

    def redraw(self):
        surf = text(self.text, int(self.size), tuple(self.color), self.font_name)
        return surf


def main():
    SIZE = (1300, 800)
    display = pygame.display.set_mode(SIZE, )
    particles = ParticleSystem()
    clock = pygame.time.Clock()
    DEFAULT_FONT = pygame.font.Font(None, 42)

    snow = SNOW
    snow.set_colorkey((0, 0, 0))
    texts = [
        "Ahlan",
        "Asalaam alaikum",
        "Zdrasti",
        "Zdraveĭte",
        "Nǐ hǎo",
        "Nǐn hǎo",
        "Hallo",
        "Goede dag",
        "Hey",
        "Hello",
        "Salut",
        "Bonjour",
        "Hug",
        "Dia dhuit",
        "Hallo",
        "Guten tag",
        "Yasou",
        "Kalimera",
        "Shalom",
        "Shalom aleichem",
        "Hē",
        "Namastē",
        "Halló",
        "Góðan dag",
        "Salam!",
        "Selamat siang",
        "Ciao",
        "Salve",
        "Yā, _Yō",
        "Konnichiwa",
        "Suosdei",
        "Suostei",
        "Anyoung",
        "Anyoung haseyo",
        "Hej",
        "Cześć",
        "Cześć!",
        "Dzień dobry!",
        "Oi",
        "Olá",
        "Hei",
        "Bună ziua",
        "Privet",
        "Zdravstvuyte",
        "¿Qué tal?",
        "Hola",
        "Hujambo",
        "Habari",
        "Hej",
        "God dag",
        "Ia ora na",
        "Ia ora na",
        "Selam",
        "Merhaba",
        "Chào",
        "Xin chào",
        "Helo",
        "Shwmae",
        "Sawubona",
        "Ngiyakwemukela",
    ]
    texts_surfs = [DEFAULT_FONT.render(text, True, "white") for text in texts]

    def base(y):
        return lambda builder: (
            builder.at((-20, gauss(y, 10)), 0)
            .velocity(gauss(8, 1), 0)
            .sized(10)
            .living(120)
            .anim_shrink()
            .anim_fade()
        )

    particles.fountains = [
        ParticleFountain(
            lambda: PolygonParticle(5, "#00a590", 2).builder().apply(base(50)).build(), 1,
        ),
        ParticleFountain(lambda: CircleParticle("#c09540").builder().apply(base(150)).build(), 1, ),
        ParticleFountain(
            lambda: PolygonParticle(6, "#a400a5").builder().apply(base(250)).build(), 1,
        ),
        ParticleFountain(
            lambda: SquareParticle()
            .builder()
            .hsv(gauss(250, 15), 80, 80)
            .apply(base(350))
            .build(),
        ),
        ParticleFountain(
            lambda: PolygonParticle(randint(3, 5))
            .builder()
            .hsv(gauss(frame / 5, 8), 100, gauss(90, 5))
            .at((uniform(0, SIZE[0]), SIZE[1] + 10), gauss(-90, 5))
            .velocity(gauss(3, 0.5))
            .inner_rotation(0, gauss(0, 2))
            .anim_fade()
            .anim_shrink()
            .build(),
            15,
        ),
        ParticleFountain(
            lambda: ShardParticle("black", 2, 5)
            .builder()
            .at((SIZE[0], 0), uniform(90, 180))
            .velocity(gauss(10, 2))
            .living(30)
            .sized(gauss(15, 2))
            .anim_shrink()
            .build(),
            0.4,
        ),
        ParticleFountain(
            lambda: CircleParticle("white")
            .builder()
            .at(pygame.mouse.get_pos(), gauss(90, 10))
            .velocity(gauss(3, 0.5))
            .anim_fade()
            .build(),
            2,
        ),
        ParticleFountain(
            lambda: SquareParticle("white")
            .builder()
            .at((uniform(0, SIZE[0]), uniform(0, SIZE[1])), 0)
            .velocity(0)
            .living(randint(100, 180))
            .sized(uniform(1, 4))
            .anim_blink()
            .build(),
        ),
        ParticleFountain(
            lambda: LineParticle(100, "#fff397", 2)
            .builder()
            .at(rand2d(SIZE), 30)
            .living(60)
            .velocity(gauss(12, 1))
            .anim_blink()
            .build(),
            0.02,
        ),
        ParticleFountain(
            lambda: ImageParticle(choice(texts_surfs))
            .builder()
            .at(pygame.mouse.get_pos() + Vector2(gauss(0, 30), -30), -90)
            .velocity(gauss(1, 0.2))
            .sized(30)
            .anim_fade()
            # .anim_shrink()
            .build(),
            0.02,
        ),
        ParticleFountain(
            lambda: ImageParticle(snow)
            .builder()
            .at((uniform(0, SIZE[0]), -20), gauss(75, 2))
            .sized(20)
            .velocity(gauss(2.5, 0.1))
            .living(240)
            .anim_fade()
            .build(),
        ),
    ]

    gfx = GFX(display)

    start = time()
    frame = 0
    running = True
    do_logic = True
    while running:
        frame += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif key == pygame.K_SPACE:
                    do_logic = not do_logic
                elif key == pygame.K_g:
                    particles.use_gfx = not particles.use_gfx
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for _ in range(200):
                    angle = uniform(0, 360)
                    particles.add(
                        CircleParticle()
                        .builder()
                        .hsv(angle)
                        .at(event.pos, angle)
                        .velocity(gauss(10, 0.5))
                        # .acceleration(-0.05)
                        .anim_shrink()
                        .anim_bounce_rect(((0, 0), SIZE))
                        .build()
                    )

        if do_logic:
            particles.logic()

        display.fill("#282832")
        particles.draw(gfx)

        s = DEFAULT_FONT.render(
            f"FPS: {clock.get_fps():.2f}  Particles: {len(particles)}", True, "white"
        )
        display.blit(s, (5, 5))

        pygame.display.update()
        clock.tick(1000)

    end = time()
    print(f"Ran for {end - start:.2f} seconds at {frame / (end - start):.2f} FPS.")


if __name__ == "__main__":
    main()
