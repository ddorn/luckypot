from pathlib import Path

from collections import defaultdict
from math import cos, pi, sin
from random import gauss, randrange, uniform

import pygame
import pygame.gfxdraw

from luckypot import *

assets.set_assets_dir(Path(__file__).parent / "assets")

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
        self.particles = ParticleSystem()
        self.particles.fountains = [
            ParticleFountain(
                lambda: SquareParticle("white")
                .builder()
                .at((uniform(0, W), uniform(0, H / 2)))
                .velocity(0)
                .sized(randrange(1, 3))
                .living(180)
                .anim_blink()
                .build(),
                0.5,
            ),
            # ParticleFountain(
            #     lambda: LineParticle(gauss(8, 1), LINES)
            #     .builder()
            #     .at(
            #         (x := (uniform(0, W), H / 2 + H / 2 * random() ** 2)),
            #         180 - (infinity - x).angle_to((1, 0)),
            #     )
            #     .living(100)
            #     .velocity(1, 0)
            #     .anim_blink(0.2, 0.5)
            #     .build()
            # ),
        ]

        self.add(Bird((0.6 * W, 30)))
        self.add(Bird((0.6 * W - 18, 30), True))
        self.add(Boids())

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
        self.particles.logic()

    def draw(self, gfx: "GFX"):

        for y in range(0, H // 2, band_height):
            color = utils.mix(SKY_TOP, SKY_END, y / H * 2)
            gfx.surf.fill(color, (0, y, W, band_height))

        self.particles.draw(gfx)

        # Sun rays and sun
        self.draw_rays(gfx, infinity, SUN_BOTTOM + (50,))
        gfx.blit(self.draw_sun(54), center=infinity)
        # Second sun
        other = (W, -15)
        self.draw_rays(gfx, other, SUN_TOP + (30,))
        gfx.blit(self.draw_sun(4 * 9, SUN_TOP, SUN_TOP), center=other)

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

        super(Sunset, self).draw(gfx)

        if "DRAW MENU":
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

        for _ in rrange(1.3):
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
        self.anim = Animation("bird idle", self.flip)

    def logic(self):
        super().logic()
        self.anim.update()

    def draw(self, gfx):
        gfx.blit(self.anim.image(), midbottom=self.pos)


class Boid:
    AVOID_STRENGTH = 0.1
    AVOID_RADIUS = 10
    ALIGN_STRENGTH = 0.05
    ALIGN_RADIUS = 20
    COHESION_STRENGTH = 0.01
    COHESION_RADIUS = 30

    WALL_RADIUS = 50
    WALL_STRENGTH = 0.04

    PLAY_RECT = pygame.Rect(0, 0, W, H / 2)
    WALLS = pygame.Rect(PLAY_RECT).inflate(-2 * WALL_RADIUS, -2 * WALL_RADIUS)

    def __init__(self, pos):
        self.max_speed = 3
        self.pos = pygame.Vector2(pos)
        a = uniform(0, 360)
        self.vel = utils.from_polar(self.max_speed, a)
        assert abs(a - self.angle) < 0.00001
        self.angle += 0

    @property
    def angle(self):
        return (-self.vel.angle_to((1, 0))) % 360

    @angle.setter
    def angle(self, value):
        self.vel.from_polar((self.vel.length(), value))

    @property
    def speed(self):
        return self.vel.length()

    @speed.setter
    def speed(self, value):
        self.vel.scale_to_length(value)

    def flockmates(self, all_boids: "SpaceHash", dist):
        x, y = self.grid(all_boids.case_size)
        return [
            boid
            for boid in all_boids.neighbors(x, y)
            if boid.pos.distance_to(self.pos) < dist and boid is not self
        ]

    def logic(self, all_boids: "SpaceHash"):
        acc = pygame.Vector2()

        acc += self.avoid(all_boids)
        acc += self.align(all_boids)
        acc += self.cohesion(all_boids)
        acc += self.walls()

        self.acc = acc
        self.vel += acc
        if self.vel.length() > self.max_speed:
            self.speed = self.max_speed
        self.pos += self.vel

    def avoid(self, all_boids):
        # Assuming there is only one boid

        force = pygame.Vector2()
        for boid in self.flockmates(all_boids, self.AVOID_RADIUS):
            dist = self.pos.distance_to(boid.pos)
            force += (self.pos - boid.pos) / dist ** 2

        return force * self.AVOID_STRENGTH

    def align(self, all_boids):
        alignment = self.flockmates(all_boids, self.ALIGN_RADIUS)
        if not alignment:
            return pygame.Vector2()

        avg_vel = sum((b.vel for b in alignment), start=pygame.Vector2())
        avg_vel.scale_to_length(self.max_speed)
        steering = avg_vel - self.vel

        return steering * self.ALIGN_STRENGTH

    def cohesion(self, all_boids):
        cohesion = self.flockmates(all_boids, self.COHESION_RADIUS)
        if not cohesion:
            return pygame.Vector2()

        center_of_mass = sum((b.pos for b in cohesion), start=pygame.Vector2()) / len(
            cohesion
        )
        vec_to_center = center_of_mass - self.pos
        if vec_to_center:
            vec_to_center.scale_to_length(self.max_speed)
        steering = vec_to_center - self.vel

        return steering * self.COHESION_STRENGTH

    def walls(self):
        distances = [*self.pos, *(self.PLAY_RECT.bottomright - self.pos)]
        normals = [
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
        ]
        steering = pygame.Vector2()
        for dist, normal in zip(distances, normals):
            if dist < self.WALL_RADIUS:
                # We project the normal on the velocity ro make it steer away
                dir = self.vel.normalize()
                avg = (
                    1 - self.WALL_STRENGTH
                ) * dir + self.WALL_STRENGTH * pygame.Vector2(normal)
                avg.scale_to_length(self.max_speed)
                steering += avg - self.vel
                continue
                dot = dir.dot(normal)
                if abs(dot) > 0.999:
                    perp = pygame.Vector2(dir.y, -dir.x)
                else:
                    perp = dir - pygame.Vector2(normal) * dot
                steering += perp / dist

        return steering

    def grid(self, case_size):
        return (self.pos.x // case_size, self.pos.y // case_size)


class SpaceHash(defaultdict):
    def __init__(self, boids, case_size):
        super().__init__(list)
        self.case_size = case_size

        for boid in boids:
            pos = boid.grid(case_size)
            self[pos].append(boid)

    def neighbors(self, x, y):
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                yield from iter(self[x + dx, y + dy])


class Boids(Object):
    def __init__(self, n_boids=300):
        super().__init__((0, 0))
        self.boids = [Boid((uniform(0, W), uniform(0, H / 2))) for _ in range(n_boids)]

    def logic(self):
        case_size = max(Boid.ALIGN_RADIUS, Boid.AVOID_RADIUS, Boid.COHESION_RADIUS) / 2
        spatial_hash = SpaceHash(self.boids, case_size)

        for boid in self.boids:
            boid.logic(spatial_hash)

    def draw(self, gfx):
        for boid in self.boids:
            pygame.draw.rect(gfx.surf, BG_COLOR, (boid.pos, (2, 2)))

        for b in self.boids[:0]:
            pygame.draw.circle(gfx.surf, "red", b.pos, b.AVOID_RADIUS, 1)
            pygame.draw.circle(gfx.surf, "yellow", b.pos, b.ALIGN_RADIUS, 1)
            pygame.draw.circle(gfx.surf, "green", b.pos, b.COHESION_RADIUS, 1)
            pygame.draw.line(gfx.surf, "blue", b.pos, b.pos + 10 * b.vel)
            pygame.draw.line(gfx.surf, "orange", b.pos, b.pos + 1000 * b.acc)
            pygame.draw.rect(
                gfx.surf, "violet", b.WALLS, 1,
            )



class SunsetApp(App):
    INITIAL_SIZE = SIZE
    INITIAL_STATE = Sunset


def main():
    SunsetApp().run()

if __name__ == "__main__":
    main()
