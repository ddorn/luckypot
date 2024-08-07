import os
import sys
from time import time
from typing import Type

import pygame
import pygame._sdl2 as sdl2

from .gfx import GFX
from .state_machine import StateMachine, StateOperations, BasicState

__all__ = ["App", "AppState"]


if os.environ.get("SDL_VIDEODRIVER") == "wayland":
    os.environ["SDL_VIDEODRIVER"] = "x11"


class AppState(BasicState):
    """Base class for all the states in the app.

    Override logic, draw, handle_events, resize and paused_logic to implement
    the state's behavior.

    See Also:
        - `state.State` for a base state with objects, particles and
            pygame-input support.
    """

    FPS = 60

    def logic(self):
        """All the logic of the state happens here.

        To change to another state, you need to call any of:
            - self.pop_state()
            - self.push_state(new)
            - self.replace_state(new)
        """

    def paused_logic(self):
        """Logic that happens when the state is not the current state."""

    def draw(self, gfx: GFX):
        """Draw the state and all its objects."""

    def handle_event(self, event) -> bool:
        """Handle a single event for the state.

        Return True if the event was handled and should not be propagated.
        """

        if event.type == pygame.QUIT:
            App.MAIN_APP.quit()
            return True

        return False

    def handle_events(self, events):
        """Handle events for the state.

        Called once per frame, even if there are no events.
        Prefer handle_event the list of events is not needed.
        """

    def resize(self, old, new):
        """Called when the window is resized from old to new."""


class App[S: AppState](StateMachine[S]):
    """
    The app is the largest element in the game, as it contains everything else.

    The purpose of the class is to:
        - handle the main loop
        - orchestrate the dance between the StateMachine, the Screen and the GFX

    All the game logic and randering is done by the states themselves.
    """

    NAME = "Pygame window"
    INITIAL_STATE: type[S] = AppState  # type: ignore
    INITIAL_SIZE = (200, 100)

    MOUSE_VISIBLE = True
    USE_FPS_TITLE = False
    WINDOW_KWARGS = {}
    GFX_CLASS = GFX

    MAIN_APP: "App" = None  # type: ignore

    def __init__(self):
        App.MAIN_APP = self

        self.clock = pygame.time.Clock()
        self.window = pygame.Window(
            title=self.NAME,
            size=self.INITIAL_SIZE,
            **self.WINDOW_KWARGS,
        )
        self.gfx = self.GFX_CLASS(self.window.get_surface())

        pygame.mouse.set_visible(self.MOUSE_VISIBLE)

        super().__init__(self.INITIAL_STATE)

    def run(self):
        """The main loop of the app."""
        pygame.init()

        frame = 0
        start = time()
        while self.state is not None:  # Equivalent to self.running
            self.handle_events()
            for state in self.stack[:-1]:
                state.paused_logic()
            self.logic()
            self.draw()
            self.window.flip()

            self.clock.tick(self.state.FPS)
            if self.USE_FPS_TITLE:
                pygame.display.set_caption(f"{self.NAME} - {self.clock.get_fps():.1f} FPS")

            frame += 1
            self.go_to_next_state()

        duration = time() - start
        print(f"Game played for {duration:.2f} seconds, at {frame / duration:.1f} FPS.")

    def draw(self):
        """Draw the current state."""
        if self.state is not None:
            self.state.draw(self.gfx)

    def logic(self):
        """Logic for the app."""
        if self.state is not None:
            self.state.logic()

    def handle_event(self, event) -> bool:
        """Handle a single event for the app.

        Return True if the event was handled and should not be propagated.
        """
        if event.type == pygame.QUIT:
            self.quit()
            return True
        elif event.type == pygame.VIDEORESIZE:
            old = self.window.size
            self.window.size = event.size
            self.gfx = self.GFX_CLASS(self.window.get_surface())
            new = self.window.size
            if old != new and self.state is not None:
                self.state.resize(old, new)

            # We want this event to propagate to the state
            return False
        elif self.state is not None:
            return self.state.handle_event(event)
        return False

    def handle_events(self):

        events = []
        for event in pygame.event.get():
            if not self.handle_event(event):
                events.append(event)

        if self.state is not None:
            self.state.handle_events(events)

    @classmethod
    def current_state(cls):
        """Current state of the main app."""
        return cls.MAIN_APP.state

    def quit(self):
        """Properly exit the app."""

        while self.stack:
            self.execute_state_transition(StateOperations.POP, None)

        self.on_exit()
        sys.exit()

    def on_exit(self):
        """Called when the app is about to exit."""


if __name__ == "__main__":
    from .state import State

    class MyState(State):
        BG_COLOR = "#60a450"

        def draw(self, gfx: GFX):
            super().draw(gfx)

            gfx.rect("blue", 0, 0, 100, 100, 5)

    class MyApp(App):
        NAME = "My app"
        INITIAL_SIZE = (500, 500)
        INITIAL_STATE = MyState
        WINDOW_KWARGS = dict(
            resizable=True,
            always_on_top=True,
        )

    MyApp().run()