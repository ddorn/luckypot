from __future__ import annotations

from enum import Enum
from random import randint
from typing import List, Optional, Tuple, Type, TypeVar, Union, TYPE_CHECKING

from pygame.locals import *

from .assets import play
from .constants import *
from .debug import Debug
from .gfx import GFX
from .object import Scriptable
from .particles import ParticleSystem
from .pygame_input import Button, Inputs, JoyButton, QuitEvent
from .settings import settings

if TYPE_CHECKING:
    from .object import Object

TObject = TypeVar("TObject", bound="Object")

__all__ = ["State", "StateMachine", "StateOperations"]


class StateOperations(Enum):
    """Operations that can be performed on a state stack."""

    NOP = 0
    POP = 1
    PUSH = 2
    REPLACE = 3


class State(Scriptable):
    FPS = 60
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
        self.next_state = (StateOperations.NOP, self)

        self.shake = 0
        self.shake_strength = 3

        self.particles = ParticleSystem()

        self.debug = self.add(Debug())

        self.inputs = Inputs()

        self.add_script(self.script())

    def create_inputs(self) -> Inputs:
        pygame.joystick.init()
        nb = pygame.joystick.get_count()
        self.debug.text("Joysticks:", nb)
        if nb > 0:
            joy = pygame.joystick.Joystick(0)
            joy.init()
            self.joy = joy

        inputs = Inputs()
        inputs["quit"] = Button(QuitEvent(), K_ESCAPE, K_q, JoyButton(JOY_BACK))
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
        self.inputs = self.create_inputs()
        self.next_state = (StateOperations.NOP, None)
        self.debug.paused = False
        if self.BG_MUSIC and not settings.mute:
            pygame.mixer.music.load(MUSIC / self.BG_MUSIC)
            # pygame.mixer.music.set_volume(VOLUME['BG_MUSIC'] * Settings().music)
            pygame.mixer.music.play(-1)

    def on_exit(self):
        """Called when the state is about to not be the current state anymore.
        It can have been popped, replaced or another state was pushed."""
        self.debug.paused = True

    # noinspection PyMethodMayBeStatic
    def script(self):
        """Script must be a generator where each yield will correspond to a frame.

        Useful to implement sequential logics.
        """
        yield

    def paused_logic(self):
        """Logic that happens when the state is not the current state."""

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
        self.inputs.trigger(events)

    def resize(self, old, new):
        """Called when the window is resized from old to new."""
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

    # State operations

    def pop_state(self, *_):
        """Return to the previous state in the state stack."""
        self.next_state = (StateOperations.POP, None)

    def push_state(self, new: "State"):
        """Add a state to the stack that will be switched to."""
        self.next_state = (StateOperations.PUSH, new)

    def replace_state(self, new: "State"):
        """Replace the current state with another one. Equivalent of a theoretic pop then push."""
        self.next_state = (StateOperations.REPLACE, new)

    def push_state_callback(self, new: Type["State"], *args):

        def callback(*_):
            # noinspection PyArgumentList
            self.next_state = (StateOperations.PUSH, new(*args))

        return callback

    def replace_state_callback(self, new: Type["State"], *args):

        def callback(*_):
            # noinspection PyArgumentList
            self.next_state = (StateOperations.REPLACE, new(*args))

        return callback


class StateMachine[S: State]:

    def __init__(self, initial_state: Type[S]):
        self._state: S | None = None
        self.stack: List[S] = []
        self.state = (StateOperations.PUSH, initial_state())

    @property
    def running(self):
        """Whether the state machine is non-empty."""
        return len(self.stack) > 0

    @property
    def state(self) -> S | None:
        """Current state. Setting needs to be done with a tuple of (StateOperations, State)."""
        if self.stack:
            return self.stack[-1]
        return None

    @state.setter
    def state(self, value: Tuple[StateOperations, S | None]):
        op, new = value

        if op == StateOperations.NOP:
            pass
        elif op == StateOperations.POP:
            assert new is None
            if self.stack:
                prev = self.stack.pop()
                prev.on_exit()
                play("back")
            if self.stack:
                self.stack[-1].on_resume()
        elif op == StateOperations.REPLACE:
            assert new is not None
            if self.stack:
                prev = self.stack.pop()
                prev.on_exit()
            self.stack.append(new)
            new.on_resume()
        elif op == StateOperations.PUSH:
            assert new is not None
            if self.stack:
                self.stack[-1].on_exit()
            self.stack.append(new)
            new.on_resume()
        else:
            print(type(op).__module__, StateOperations.__module__)
            print(type(op) == StateOperations)
            print(op, new)
            raise ValueError("Unknown operation type.")
