from typing import Optional, Tuple, TYPE_CHECKING, Generator, Callable

import pygame

from .assets import rotate
from .constants import GREEN, RED, UPWARDS
from .gfx import GFX
from .particles import TextParticle
from .utils import overlay, random_in_rect, random_rainbow_color

if TYPE_CHECKING:
    from . import State

__all__ = ["Object", "Entity", "SpriteObject", "Scriptable"]


class Scriptable:
    """Base class of most game objects.

    A Scriptable is a collection of scripts, which are generators
    and are meant to run one iteration per frame.
    A script is automatically removed when it reaches its end,
    that is, when the generator raises StopIteration

    A new script can be added to run in parallel of the other
    with .add_script().

    Objects, but also States are Scriptable.
    """

    def __init__(self):
        super().__init__()
        self.scripts = set()
        # To allow scripts to add other scripts
        self.scripts_to_add = set()
        self.script_add_lock = False

        self.add_script(self.script())

    def add_script(self, generator: Generator):
        if self.script_add_lock:
            self.scripts_to_add.add(generator)
        else:
            self.scripts.add(generator)

    def add_script_decorator(self, function):
        self.add_script(function())

    def logic(self):
        """Call the next frame of each script."""

        to_remove = set()
        self.script_add_lock = True
        for script in self.scripts:
            try:
                next(script)
            except StopIteration:
                to_remove.add(script)
        self.scripts.difference_update(to_remove)
        self.script_add_lock = False
        self.scripts.update(self.scripts_to_add)

    def do_later(self, nb_of_frames):
        """Decorator to automatically call a function :nb_of_frames: later.

        Warning: when used with objects, the script is canceled when
        the object dies and is removed from the state. For a script
        to outlive its object, it has to be registred on the state directly.

        Examples:
            Write "BOOOM" after 60 frames:
            >>> object = Scriptable()
            >>> @object.do_later(60)
            >>> def explode():
            >>>     print("BOOOOM")
        """

        def decorator(func):

            def script():
                yield from range(nb_of_frames)
                func()

            self.add_script(script())
            return func

        return decorator

    def wait_until(self, condition: Callable[[], bool]) -> Generator:
        """Script that wait and does nothing until the condition is met."""
        while not condition():
            yield

    def script(self):
        """Script must be a generator where each yield will correspond to a frame.

        Useful to implement sequential logics.
        """
        yield




class Object(Scriptable):
    """Base class for everything in the game world."""

    Z = 0  # Z-Index to determine in which order to draw objects.

    def __init__(self, pos, size=(1, 1), vel=(0, 0)):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.size = pygame.Vector2(size)
        self.vel = pygame.Vector2(vel)
        # Should we have acceleration too ? Maybe. Idk.
        self.alive = True
        self.state: Optional["State"] = None

        # A (likely) unique color per object, that can be used for debugging
        self._random_color = random_rainbow_color(80)

        self.add_script(self.script())

    def __str__(self):
        return f"{self.__class__.__name__}(at {self.pos})"

    def script(self):
        """Override this generator to add a script to the objects.

        Other scripts/generators can be added with .add_script()"""
        yield

    def wait_until_dead(self):
        """Script that wait and does nothing while the object is alive."""
        while self.alive:
            yield

    @property
    def center(self):
        return self.pos + self.size / 2

    @center.setter
    def center(self, value: pygame.Vector2):
        self.pos = value - self.size / 2

    @property
    def rect(self):
        return pygame.Rect(self.pos, self.size)

    def logic(self):
        """Override this with the logic needed to evolve the object to the next frame.

        Don't forget to call super().logic() !!
        """

        super().logic()

        self.pos += self.vel

        self.state.debug.rectangle(self.rect, self._random_color)
        self.state.debug.vector(self.vel * 10, self.center, self._random_color)

    def draw(self, gfx: GFX):
        """Override this to draw the object on the screen every frame."""

    def on_death(self):
        """Method called whenever the object dies."""

    def resize(self, old, new):
        """Called every time the window resizes.

        This should not have any impoact on position/speed,
        as they should not depend on the window size. Instead
        this should handle the different sprite sizes (for instance)

        Args:
            old (pygame.Vector2): previous size of the window
            new (pygame.Vector2): actual size of the window
        """

    def create_inputs(self):
        """Return an Input object that handles events for the object."""
        return {}


class SpriteObject(Object):
    # SpriteObjects are automatically scaled by this amount.
    # It is not meant to be changed at runtime.
    SCALE = 1
    # The direction that the sprite is facing in its source image.
    INITIAL_ROTATION = UPWARDS

    def __init__(
            self,
            pos,
            image: pygame.Surface,
            offset=(0, 0),
            size: Optional[Tuple[int, int]] = None,
            vel=(0, 0),
            rotation=0,
    ):
        """
        An object with an image.

        Args:
            pos: position of the object in world coordinates, the topleft of its hitbox
            image: sprite drawn every frame
            offset: vector between the topleft of the image to the topleft of the hitbox, in pixels.
                Usually negative numbers, as the hitbox is smaller than the sprite.
            size: Size of the hitbox
            vel: initial velocity
            rotation: initial rotation of the image
        """

        if self.SCALE > 1:
            image = pygame.transform.scale(
                image, (self.SCALE * image.get_width(), self.SCALE * image.get_height()))
        if size is None:
            size = image.get_size()

        self.base_image = image
        self.image_offset = pygame.Vector2(offset)
        self.rotation = rotation
        self.opacity = 255

        super().__init__(pos, size, vel)

    @property
    def angle(self):
        return (-self.rotation + self.INITIAL_ROTATION) % 360

    @angle.setter
    def angle(self, value):
        self.rotation = -value + self.INITIAL_ROTATION

    @property
    def image(self):
        img = rotate(self.base_image, int(self.rotation))
        img.set_alpha(self.opacity)
        return img

    def draw(self, gfx: "GFX"):
        super().draw(gfx)
        gfx.blit(self.image, center=self.sprite_center)

    @property
    def sprite_center(self):
        """Position of the center of the sprite, in world coordinates."""
        return (self.pos + self.image_offset * self.SCALE +
                pygame.Vector2(self.base_image.get_size()) / 2)

    def sprite_to_screen(self, pos):
        """Convert a position in the sprite to its world coordinates."""
        pos = (
            pygame.Vector2(pos) + (0.5, 0.5)  # To get the center of the pixel
            - pygame.Vector2(self.base_image.get_size()) / 2 / self.SCALE)
        pos.rotate_ip(-self.rotation)
        pos *= self.SCALE
        r = self.sprite_center + pos
        return r


# This class might be a bit specific for Flyre,
# but I leave it there as a base for a future class.


class Entity(SpriteObject):
    """An object with health and a sprite."""

    INVICIBILITY_DURATION = 0
    INITIAL_LIFE = 1000

    def __init__(
            self,
            pos,
            image: pygame.Surface,
            offset=(0, 0),
            size=(1, 1),
            vel=(0, 0),
            rotation=0,
    ):
        super().__init__(pos, image, offset, size, vel, rotation)
        self.max_life = self.INITIAL_LIFE
        self.life = self.INITIAL_LIFE
        self.last_hit = 100000000

    def heal(self, amount):
        if self.life + amount > self.max_life:
            amount = self.max_life - self.life

        if amount <= 0:
            return

        self.life += amount

        pos = random_in_rect(self.rect)
        # fmt: off
        self.state.particles.add(
            TextParticle(str(int(amount)), GREEN)
            .builder()
            .at(pos, 90)
            .velocity(0)
            .sized(15)
            .anim_fade(0.5)
            .anim_bounce_size_and_shrink()
            .build()
        )
        # fmt: on

    def damage(self, amount, ignore_invincibility=False):
        if amount < 0:
            self.heal(amount)
            return

        if self.invincible and not ignore_invincibility:
            return

        # amount *= gauss(1, 0.1)

        self.last_hit = 0

        self.life -= amount
        if self.life < 0:
            self.life = 0
            self.alive = False

        pos = random_in_rect(self.rect)
        # fmt: off
        self.state.particles.add(
            TextParticle(str(int(amount)), RED)
            .builder()
            .at(pos, 90)
            .velocity(0)
            .sized(15)
            .anim_fade(0.5)
            .anim_bounce_size()
            .build()
        )
        # fmt: on

    def logic(self):
        super().logic()

        self.last_hit += 1

        if self.life <= 0:
            self.alive = False

    def draw(self, gfx):
        if self.last_hit < 3:
            gfx.surf.blit(
                overlay(self.image, RED),
                self.image.get_rect(center=self.sprite_center),
            )
            return

        if self.invincible and self.last_hit % 6 > 3:
            return  # no blit

        super().draw(gfx)

    @property
    def invincible(self):
        return self.last_hit < self.INVICIBILITY_DURATION
