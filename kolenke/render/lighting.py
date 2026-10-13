"""Жарықтандыру (multiply-маска), виньетка. Қараңғы түн атмосферасы үшін."""
import math

import pygame


class Lighting:
    """Қараңғы қабат: ambient + қосылатын жарық дақтары, сосын сахнаға көбейтіледі."""

    def __init__(self, size, ambient=(16, 18, 28)):
        self.size = size
        self.ambient = ambient
        self.dark = pygame.Surface(size)
        self._cache = {}

    def _light_surface(self, radius, color, intensity):
        radius = max(16, int(radius) // 8 * 8)
        level = int(intensity * 8)
        key = (radius, color, level)
        if key not in self._cache:
            base = pygame.Surface((64, 64))
            k = level / 8.0
            for i in range(32, 0, -1):
                f = (1 - i / 32) ** 1.5 * k
                pygame.draw.circle(base, tuple(min(255, int(c * f)) for c in color),
                                   (32, 32), i)
            self._cache[key] = pygame.transform.smoothscale(base, (radius * 2, radius * 2))
        return self._cache[key], radius

    def render(self, screen, lights, cam_x, t=0.0, offset=(0, 0)):
        """lights: dict(x, y, r, color, i, flicker, seed) тізімі."""
        self.dark.fill(self.ambient)
        w = self.size[0]
        for L in lights:
            sx = L["x"] - cam_x
            if sx + L["r"] < 0 or sx - L["r"] > w:
                continue
            inten = L["i"] * (1 - L.get("flicker", 0) * self.noise(t, L.get("seed", 0)))
            surf, r = self._light_surface(L["r"], L["color"], max(0.05, inten))
            self.dark.blit(surf, (sx - r, L["y"] - r), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(self.dark, offset, special_flags=pygame.BLEND_RGB_MULT)

    @staticmethod
    def noise(t, seed):
        """0..1 мерцание: көбіне тыныш, кейде күрт сөнеді."""
        a = math.sin(t * 13 + seed) * math.sin(t * 7.3 + seed * 2.1)
        return max(0.0, abs(a) - 0.35) / 0.65


def make_vignette(size, strength=215):
    small = pygame.Surface((64, 36), pygame.SRCALPHA)
    for y in range(36):
        for x in range(64):
            dx, dy = (x / 63 - 0.5) * 2, (y / 35 - 0.5) * 2
            r = min(1.0, math.hypot(dx, dy) / 1.38)
            a = int(strength * (max(0.0, r - 0.42) / 0.58) ** 2)
            small.set_at((x, y), (0, 0, 0, a))
    return pygame.transform.smoothscale(small, size)
