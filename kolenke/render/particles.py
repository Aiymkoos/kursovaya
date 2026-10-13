"""Бөлшектер жүйесі: жалпы (шаң, ұшқын, көлеңке) және боран."""
import math
import random


class ParticleSystem:
    """Қарапайым бөлшектер: орны, жылдамдығы, өмірі, өлшемі, түсі."""

    def __init__(self, limit=400):
        self.limit = limit
        self.items = []  # [x, y, vx, vy, life, max_life, size, color, gravity]

    def emit(self, x, y, vx, vy, life, size, color, gravity=0.0):
        if len(self.items) < self.limit:
            self.items.append([x, y, vx, vy, life, life, size, color, gravity])

    def update(self, dt):
        alive = []
        for p in self.items:
            p[4] -= dt
            if p[4] > 0:
                p[3] += p[8] * dt
                p[0] += p[2] * dt
                p[1] += p[3] * dt
                alive.append(p)
        self.items = alive

    def draw(self, surface, cam_x=0.0):
        for x, y, _, _, life, max_life, size, color, _ in self.items:
            k = life / max_life  # өшу: түсті қараңғыға қарай азайту
            c = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
            r = max(1, int(size * (0.4 + 0.6 * k)))
            surface.fill(c, (int(x - cam_x), int(y), r, r))


class Blizzard:
    """Экран кеңістігіндегі боран: терезе артында немесе фонда."""

    def __init__(self, width, height, count=200, wind=-140, seed=7):
        rng = random.Random(seed)
        self.w, self.h, self.wind = width, height, wind
        self.flakes = [[rng.uniform(0, width), rng.uniform(0, height),
                        rng.uniform(90, 260), rng.choice((1, 2, 2, 3, 4)),
                        rng.uniform(0, 6.28)] for _ in range(count)]
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        for f in self.flakes:
            f[1] += f[2] * dt
            f[0] += (self.wind + math.sin(self.t * 1.3 + f[4]) * 45) * dt * (f[3] / 2.5)
            if f[1] > self.h:
                f[1] -= self.h
            if f[0] < 0:
                f[0] += self.w
            elif f[0] > self.w:
                f[0] -= self.w

    def draw(self, surface, brightness=1.0, offset=(0, 0)):
        ox, oy = offset
        for x, y, _, size, _ in self.flakes:
            v = min(255, int((110 + 36 * size) * brightness))
            surface.fill((v, v, min(255, v + 12)), (int(x + ox), int(y + oy), size, size))
