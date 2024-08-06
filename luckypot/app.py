import os
import sys
from time import time
from typing import Type

import pygame
import pygame._sdl2 as sdl2

from .gfx import GFX
from .settings import settings
from .state_machine import GAME_NAME, State, StateMachine, StateOperations

__all__ = ["App"]


if os.environ.get("SDL_VIDEODRIVER") == "wayland":
    os.environ["SDL_VIDEODRIVER"] = "x11"


class App(StateMachine):
    """
    The app is the largest element in the game, as it contains everything else.

    The purpose of the class is to:
        - handle the main loop
        - orchestrate the dance between the StateMachine, the Screen and the GFX

    All the game logic and randering is done by the states themselves.
    """

    NAME = "Pygame window"
    MAIN_APP: "App" = None
    MOUSE_VISIBLE = True
    USE_FPS_TITLE = False
    INITIAL_SIZE = (200, 100)
    INITIAL_STATE = State
    WINDOW_KWARGS = {}
    GFX_CLASS = GFX

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
            self.state = self.state.next_state

        duration = time() - start
        print(f"Game played for {duration:.2f} seconds, at {frame / duration:.1f} FPS.")
        settings.save()

    def events(self):
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
            self.state = (StateOperations.POP, None)

        settings.save()

        sys.exit()


if __name__ == "__main__":

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