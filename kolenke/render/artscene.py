"""Жүру сахнасының дайын суретті фоны (assets/bg/*.png): параллакс және есік белгілері.

Фон файлы болмаса — ArtBackdrop.load None қайтарады, сахна кодпен сызылған декорацияны қолданады.
"""
import math

import pygame

from kolenke.core.assets import load_image

H = 720
# локация id -> assets/bg/<файл>.png
ART_FILES = {"corridor": "corridor", "darkhan_room": "room_darkhan",
             "girls_room": "room_girls", "bekzat_room": "room_bekzat"}
ZOOM = {"corridor": 1.28, "darkhan_room": 1.06, "girls_room": 1.06, "bekzat_room": 1.06}
AMBIENT = (205, 208, 226)      # сурет өз жарығын сақтасын: аздап қана қараңғылау
_glow_cache = {}


class ArtBackdrop:
    def __init__(self, surface, loc_width, screen_w):
        self.img = surface
        self.loc_width = loc_width
        self.screen_w = screen_w
        self.span = max(0, surface.get_width() - screen_w)

    @classmethod
    def load(cls, loc, screen_size):
        name = ART_FILES.get(loc.id)
        if not name:
            return None
        w, h = screen_size
        art = load_image(f"bg/{name}")
        if art is None:
            return None
        k = h * ZOOM.get(loc.id, 1.06) / art.get_height()
        size = (max(w, round(art.get_width() * k)), round(art.get_height() * k))
        scaled = pygame.transform.smoothscale(art, size)
        return cls(scaled, loc.width, w)

    def draw(self, surface, cam, player_x):
        """Параллакс: ұзын локацияда камераға, бөлмеде кейіпкер орнына қарай жылжиды."""
        scroll = max(1, self.loc_width - self.screen_w)
        frac = cam / scroll if self.loc_width > self.screen_w else player_x / max(1, self.loc_width)
        x = -int(max(0.0, min(1.0, frac)) * self.span)
        y = -(self.img.get_height() - H)             # төменгі жағына тураланады (еден көрінеді)
        surface.blit(self.img, (x, y))


def _door_glow(width, height):
    key = (width, height)
    if key not in _glow_cache:
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(height):
            fade = (i / height) ** 1.8                 # жоғарыдан төмен күшейеді, есіктің табанына жарық
            pygame.draw.line(surf, (255, 214, 150, int(70 * fade)), (width // 6, i), (width * 5 // 6, i))
        surf = pygame.transform.smoothscale(surf, (width // 3, height // 3))     # жиектерін бұлыңғыр ету
        surf = pygame.transform.smoothscale(surf, (width, height))
        _glow_cache[key] = surf
    return _glow_cache[key]


def draw_door_marker(surface, x, ground_y, w, t):
    """Есік орнында жұмсақ жарқыраған жақтау: суретте есік басқа жерде болса да, қайда кіруге болатыны көрінеді."""
    width, height = int(w * 1.1), 300
    pulse = 0.8 + 0.2 * math.sin(t * 2.4 + x * 0.01)
    glow = _door_glow(width, height).copy()
    glow.fill((255, 255, 255, int(255 * pulse)), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(glow, glow.get_rect(midbottom=(x, ground_y - 10)))
