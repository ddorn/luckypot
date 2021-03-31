from math import cos, pi, sin
from random import gauss, random, randrange, uniform

import pygame
import pygame.gfxdraw

import assets
from engine import *
from particles import rrange

R = 40
W, H = SIZE = (16 * R, 9 * R)
print(SIZE)

SUN_TOP = (255, 218, 69)
# SUN_TOP = (255, 129, 66)
SUN_BOTTOM = (255, 79, 105)
SKY_END = (171, 31, 101)
SKY_TOP = (73, 231, 236)
LINES = (255, 79, 105)
BG_COLOR = (43, 15, 84)
band_height = 9
infinity = pygame.Vector2(W / 4, H * 0.46 // band_height * band_height,)


class Sunset(State):
    BG_COLOR = None

    def __init__(self):
        super().__init__()
        # self.particles = ParticleSystem()
        # self.particles.fountains = [
        #     ParticleFountain(
        #         lambda: SquareParticle("white")
        #         .builder()
        #         .at((uniform(0, W), uniform(0, H / 2)))
        #         .velocity(0)
        #         .sized(randrange(1, 3))
        #         .living(180)
        #         .anim_blink()
        #         .build(),
        #         0.5,
        #     ),
        #     ParticleFountain(
        #         lambda: LineParticle(gauss(8, 1), LINES)
        #         .builder()
        #         .at(
        #             (x := (uniform(0, W), H / 2 + H / 2 * random() ** 2)),
        #             180 - (infinity - x).angle_to((1, 0)),
        #         )
        #         .living(100)
        #         .velocity(1, 0)
        #         .anim_blink(0.2, 0.5)
        #         .build()
        #     ),
        # ]

        self.add(Bird((0.6 * W, 30)))
        self.add(Bird((0.6 * W - 18, 30), True))

    def draw_sun(self, radius=50, top=SUN_TOP, bottom=SUN_BOTTOM, alpha=255):
        size = radius * 2 + 1, radius * 2 + 1
        sun = pygame.Surface(size)
        mask = pygame.Surface(size)

        # Defining the shape of the sun
        pygame.draw.circle(
            mask, "white", (radius, radius), radius,
        )
        # Removing bands
        y = 9
        s = 3
        while y < size[1]:
            pygame.gfxdraw.hline(mask, 0, size[1], y, (0, 0, 0))
            y += 9
            # s += 1

        # Defining the color of the sun
        color = top
        for y in range(0, size[1]):
            if y % 9 == 0:
                color = utils.mix(top, bottom, y / size[1])
            pygame.gfxdraw.hline(sun, 0, size[1], y, color)

        sun.blit(mask, (0, 0), special_flags=pygame.BLEND_MULT)
        sun.set_colorkey(0)
        sun.set_alpha(alpha)
        return sun

    def draw_rays(self, gfx, center, color=SUN_BOTTOM):
        for angle in range(0, 360, 10):
            angle += self.timer / 7
            span = 5
            p1 = center + utils.from_polar(1000, angle - span / 2)
            p2 = center + utils.from_polar(1000, angle + span / 2)
            points = [center, p1, p2]
            pygame.gfxdraw.filled_polygon(gfx.surf, points, color)

    def logic(self):
        super().logic()
        # self.particles.logic()

    def draw(self, gfx: "GFX"):

        for y in range(0, H // 2, band_height):
            color = utils.mix(SKY_TOP, SKY_END, y / H * 2)
            gfx.surf.fill(color, (0, y, W, band_height))

        # self.particles.draw(gfx.surf)

        # Sun rays and sun
        self.draw_rays(gfx, infinity, SUN_BOTTOM + (50,))
        gfx.blit(self.draw_sun(54), center=infinity)
        # Second sun
        # other = (W, -15)
        # self.draw_rays(gfx, other, SUN_TOP + (30,))
        # gfx.blit(self.draw_sun(4 * 9, SUN_TOP, SUN_TOP), center=other)

        second_half = pygame.Rect(0, H / 2, W, H / 2)
        gfx.surf.fill(BG_COLOR, second_half)

        # Horizontal lines
        y = H
        prop = 3 / 4
        dy = (-self.timer / 1) % (H / 2 * (1 - prop))
        n = -1
        while y > H / 2:
            pygame.gfxdraw.hline(gfx.surf, 0, W, round(y), LINES)
            y = infinity[1] + (H / 2 - dy) * (prop ** n)
            n += 1
        pygame.gfxdraw.hline(gfx.surf, 0, W, H // 2, LINES)

        # Vertical lines
        n_lines = 17
        for n in range(n_lines):
            n = utils.chrange(n, (0, n_lines - 1), (-pi / 2, pi / 2))
            angle = utils.chrange(sin(n), (-1, 1), (0, pi))

            x = infinity[0] + 1000 * cos(angle)
            y = infinity[1] + 1000 * sin(angle)

            line = second_half.clipline(x, y, *infinity)
            if line:
                pygame.draw.line(gfx.surf, LINES, *line)
            # pygame.draw.line(gfx.surf, LINES, infinity, (x, y))

        # self.particles.draw(gfx.surf)

        margin = 30
        menu_rect = pygame.Rect(
            W / 2 + margin, margin, W / 2 - 2 * margin, H - margin * 2
        )
        menu_rect.midright = W - margin, H / 2
        pygame.gfxdraw.box(gfx.surf, menu_rect, (0, 0, 0, 125))
        pygame.draw.rect(gfx.surf, utils.mix(SUN_TOP, SUN_BOTTOM, 0.5), menu_rect, 1)

        # signature
        sig = assets.image("ByCozyFractal").copy()
        sig.fill(LINES, special_flags=pygame.BLEND_ADD)
        pygame.gfxdraw.box(
            gfx.surf,
            sig.get_rect(bottomleft=(4, H - 2)).inflate(8, 4),
            BG_COLOR + (200,),
        )
        gfx.blit(sig, bottomleft=(4, H - 2))

        super(Sunset, self).draw(gfx)


class Bird(Object):
    def __init__(self, pos, flip=False):
        super().__init__(pos)

        self.flip = flip
        self.anim = Animation("bird idle", flip)
        self.scripts.add(self.script())

    def script(self):
        while True:

            if randrange(6) == 0:
                yield from self.pick()
            elif randrange(15) == 0:
                yield from self.fly()

            for _ in range(60):
                yield

    def pick(self):
        self.anim = Animation("bird pick", self.flip)

        for _ in range(len(self.anim)):
            yield

        self.anim = Animation("bird idle", self.flip)

    def fly(self):
        self.anim = Animation("bird fly", self.flip)

        start_pos = pygame.Vector2(self.pos)
        angle = 0 if self.flip else 180
        speed = 3
        screen = pygame.Rect(0, 0, W, H).inflate(32, 32)
        while screen.collidepoint(*self.pos):
            angle += uniform(-1, 1) * 3
            self.pos += utils.from_polar(speed, angle)
            yield

        for _ in range(int(gauss(6 * 60, 60))):
            yield

        # Come back to "spawn"
        dur = 20
        dir = -1 if self.flip else 1
        for i in range(dur, 0, -1):
            self.pos = start_pos + (i * 3 * dir, -(i ** 2) / 15)
            yield

        self.pos = start_pos
        self.anim = Animation("bird pick", self.flip)

    def logic(self, state):
        super().logic(state)
        self.anim.update()

    def draw(self, gfx):
        gfx.blit(self.anim.image(), midbottom=self.pos)


if __name__ == "__main__":
    pygame.init()
    App(Sunset, IntegerScaleScreen(SIZE)).run()
