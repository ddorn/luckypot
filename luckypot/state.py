from __future__ import annotations

from random import randint
from typing import TypeVar, TYPE_CHECKING

from pygame.locals import *

from .assets import play
from .constants import *
from .debug import Debug
from .gfx import GFX
from .particles import ParticleSystem
from .pygame_input import Button, Inputs, JoyButton, QuitEvent
from .settings import settings
from .app import AppState

if TYPE_CHECKING:
    from .object import Object

TObject = TypeVar("TObject", bound="Object")

class State(AppState):
    BG_COLOR = "black"
    BG_MUSIC = None
    BG_COLORS = []
    BG_TRANSITION_TIME = 20 * 60

    def __init__(self):
        super().__init__()
        self.timer = 0
        self.add_later = []
        self.add_object_lock = False
        self.objects = set()

        self.shake = 0
        self.shake_strength = 3

        self.particles = ParticleSystem()

        self.debug = self.add(Debug())

        self.inputs = Inputs()

    def create_inputs(self) -> Inputs:
        pygame.joystick.init()
        nb = pygame.joystick.get_count()
        self.debug.text("Joysticks:", nb)
        if nb > 0:
            joy = pygame.joystick.Joystick(0)
            joy.init()
            self.joy = joy

        inputs = Inputs()
        inputs["quit"] = Button(K_ESCAPE, K_q, JoyButton(JOY_BACK))
        inputs["quit"].on_press(self.pop_state)

        inputs["mute"] = Button(K_m, JoyButton(11))
        inputs["mute"].on_press(self.toggle_mute)

        for object in self.objects:
            obj_inputs = object.create_inputs()
            if not set(inputs).isdisjoint(obj_inputs):
                raise ValueError("Conflicting key inputs.")

            inputs.update(object.create_inputs())

        return inputs

    def toggle_mute(self, *_):
        settings.mute = not settings.mute
        if settings.mute:
            pygame.mixer.music.set_volume(0)
        else:
            pygame.mixer.music.set_volume(1)

    # Life phase of state

    def on_resume(self):
        """Called when the state is about to become the current state."""
        super().on_resume()
        self.inputs = self.create_inputs()
        self.debug.paused = False
        if self.BG_MUSIC and not settings.mute:
            pygame.mixer.music.load(MUSIC / self.BG_MUSIC)
            # pygame.mixer.music.set_volume(VOLUME['BG_MUSIC'] * Settings().music)
            pygame.mixer.music.play(-1)

    def on_pause(self):
        super().on_pause()
        self.debug.paused = True

    def on_exit(self):
        play("back")
        return super().on_exit()

    def logic(self):
        """All the logic of the state happens here.

        To change to another state, you need to call any of:
            - self.pop_state()
            - self.push_state(new)
            - self.replace_state(new)
        """
        super().logic()

        self.timer += 1

        self.update_bg()

        # Add all object that have been queued
        self.add_object_lock = False
        for object in self.add_later:
            self.add(object)
        self.add_later = []
        self.add_object_lock = True

        # Logic for all objects
        for object in self.objects:
            object.logic()
        self.particles.logic()

        # Clean dead objects
        to_remove = set()
        for object in self.objects:
            if not object.alive:
                to_remove.add(object)
                object.on_death()
        self.objects.difference_update(to_remove)

    def draw(self, gfx: GFX):
        """Draw the state and all its objects."""
        super().draw(gfx)

        if self.BG_COLOR:
            gfx.fill(self.BG_COLOR)

        did_draw_particles = False
        for z in sorted(set(o.Z for o in self.objects)):
            for obj in self.objects:
                if z == obj.Z:
                    obj.draw(gfx)
            # We draw particles after the 0-th layer.
            if z >= 0 and not did_draw_particles:
                self.particles.draw(gfx)
                did_draw_particles = True

        if not did_draw_particles:
            self.particles.draw(gfx)

        if self.shake:
            s = self.shake_strength
            gfx.surf.scroll(randint(-s, s), randint(-s, s))
            self.shake -= 1

    def handle_events(self, events):
        """Handle events for the state."""
        super().handle_events(events)
        self.inputs.trigger(events)

    def resize(self, old, new):
        """Called when the window is resized from old to new."""
        super().resize(old, new)
        for obj in self.objects:
            obj.resize(old, new)

    # State modifications

    def add(self, obj: TObject) -> TObject:
        """Add an object to the state.

        Note that is only added at the beginning of the next frame.
        This allows to add objects while modifying/iterating over the objects.

        Returns:
            The argument is returned, to allow creating,
            adding and storing it in a variable in the same line.
        """

        if self.add_object_lock:
            self.add_later.append(obj)
        else:
            self.objects.add(obj)

        obj.state = self

        return obj

    def get_all(self, *types):
        """Get all objects in the State with the given types.

        Types can either be classes or class names."""
        for object in self.objects:
            for t in types:
                if isinstance(t, str):
                    if any(c.__name__ == t for c in object.__class__.__mro__):
                        yield object
                        break
                elif isinstance(object, t):
                    yield object
                    break

    def do_shake(self, frames: int, strength: int | None = None):
        """Shake the screen for the given number of frames."""
        assert frames >= 0
        if strength is not None:
            self.shake_strength = strength
        self.shake += frames

    def update_bg(self):
        if self.BG_COLORS:
            first = self.timer // self.BG_TRANSITION_TIME % len(self.BG_COLORS)
            second = (first + 1) % len(self.BG_COLORS)
            t = (self.timer % self.BG_TRANSITION_TIME) / self.BG_TRANSITION_TIME
            bg = Color(self.BG_COLORS[first]).lerp(self.BG_COLORS[second], t)
            # bg = mix(self.BG_COLORS[first], self.BG_COLORS[second], t)

            self.BG_COLOR = bg