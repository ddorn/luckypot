import os
import sys
from time import time
from typing import Type

import pygame
import pygame._sdl2 as sdl2

from .gfx import GFX
from .settings import settings
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

    def handle_events(self, events):
        """Handle events for the state."""

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
            self.events()
            for state in self.stack[:-1]:
                state.paused_logic()
            self.state.logic()
            self.state.draw(self.gfx)
            self.window.flip()

            self.clock.tick(self.state.FPS)
            if self.USE_FPS_TITLE:
                pygame.display.set_caption(f"{self.NAME} - {self.clock.get_fps():.1f} FPS")

            frame += 1
            self.go_to_next_state()

        duration = time() - start
        print(f"Game played for {duration:.2f} seconds, at {frame / duration:.1f} FPS.")
        settings.save()

    def events(self):
        assert self.state is not None

        events = list(pygame.event.get())
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                old = self.window.size
                self.window.size = event.size
                self.gfx = self.GFX_CLASS(self.window.get_surface())
                new = self.window.size
                print("Resized to", new, "from", old)
                if old != new:
                    self.state.resize(old, new)

            # Was from when screen could scale the window.
            # elif event.type in (
            #         pygame.MOUSEMOTION,
            #         pygame.MOUSEBUTTONDOWN,
            #         pygame.MOUSEBUTTONUP,
            # ):
            #     self.screen.fixup_mouse_input(event)

        self.state.handle_events(events)

    @classmethod
    def current_state(cls):
        """Current state of the main app."""
        return cls.MAIN_APP.state

    def quit(self):
        """Properly exit the app."""

        while self.stack:
            self.execute_state_transition(StateOperations.POP, None)

        settings.save()

        sys.exit()


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