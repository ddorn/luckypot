import os
from time import time

import pygame
import pygame._sdl2 as sdl2

from .gfx import GFX
from .settings import settings
from .state_machine import State, StateMachine

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

    FPS = 60
    NAME = "Pygame window"
    MAIN_APP: "App" = None
    INITIAL_SIZE = (200, 100)
    INITIAL_STATE = State
    WINDOW_KWARGS = {}

    def __init__(self):
        App.MAIN_APP = self

        self.clock = pygame.time.Clock()
        self.window = pygame.Window(
            title=self.NAME,
            size=self.INITIAL_SIZE,
            **self.WINDOW_KWARGS,
        )

        self.gfx = GFX(self.window.get_surface())

        super().__init__(self.INITIAL_STATE)

    def run(self):
        """The main loop of the app."""
        pygame.init()

        frame = 0
        start = time()
        while self.running:
            self.events()
            self.state.logic()
            self.state.draw(self.gfx)
            self.window.flip()

            self.clock.tick(self.FPS)

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
                self.gfx = GFX(self.window.get_surface())
                new = self.window.size
                print("Resized to", new, "from", old)
                if old != new:
                    self.state.resize(old, new)
            # Was from when screen could scale the window.
            # elif event.type in (
            #     pygame.MOUSEMOTION,
            #     pygame.MOUSEBUTTONDOWN,
            #     pygame.MOUSEBUTTONUP,
            # ):
            #     self.screen.fixup_mouse_input(event)

        self.state.handle_events(events)


if __name__ == "__main__":

    class MyState(State):
        BG_COLOR = "#ffa450"

        def draw(self, gfx: GFX):
            super().draw(gfx)

            gfx.rect(0, 0, 10, 10, "blue", 5)

    class MyApp(App):
        NAME = "My app"
        INITIAL_SIZE = (500, 500)
        INITIAL_STATE = MyState
        WINDOW_KWARGS = dict(
            resizable=True,
            always_on_top=True,
        )

    MyApp().run()
