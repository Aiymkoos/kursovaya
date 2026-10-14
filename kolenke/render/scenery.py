"""Локация декорациялары: бір рет алдын ала сызылады (60 FPS үшін)."""
from dataclasses import dataclass, field

import pygame

H = 720
GROUND = 640       # кейіпкер табаны тұратын сызық
WALL_BOTTOM = 560


@dataclass
class Scenery:
    surface: pygame.Surface
    windows: list = field(default_factory=list)   # әлем координатасындағы Rect
    lights: list = field(default_factory=list)    # Lighting.render үшін
    pillars: list = field(default_factory=list)   # алдыңғы план бағандары (x)
    ambient: tuple = (16, 18, 28)


def _gradient(width, y0, y1, top, bottom, surf):
    for y in range(y0, y1):
        k = (y - y0) / max(1, y1 - y0 - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3))
        pygame.draw.line(surf, c, (0, y), (width, y))


def _floor(surf, width):
    _gradient(width, WALL_BOTTOM, H, (84, 66, 58), (36, 28, 26), surf)
    y, step = WALL_BOTTOM + 8, 10
    while y < H:
        pygame.draw.line(surf, (10, 8, 8), (0, y), (width, y))
        y += step
        step += 6
    for x in range(0, width, 170):
        pygame.draw.line(surf, (12, 10, 9), (x, WALL_BOTTOM), (x - 60, H))
    pygame.draw.line(surf, (60, 50, 46), (0, WALL_BOTTOM), (width, WALL_BOTTOM), 3)


def _window(surf, rect, windows):
    glass = pygame.Rect(rect)
    pygame.draw.rect(surf, (8, 10, 14), glass.inflate(16, 16), border_radius=4)
    for y in range(glass.top, glass.bottom):
        k = (y - glass.top) / glass.height
        c = (int(22 + 34 * k), int(38 + 44 * k), int(66 + 52 * k))
        pygame.draw.line(surf, c, (glass.left, y), (glass.right - 1, y))
    windows.append(glass)


def _door(surf, obj):
    x, w = obj.x, obj.w
    rect = pygame.Rect(0, 0, w, 330)
    rect.midbottom = (x, WALL_BOTTOM)
    pygame.draw.rect(surf, (12, 9, 8), rect.inflate(18, 14), border_radius=3)
    pygame.draw.rect(surf, (62, 42, 33), rect)
    for panel in (rect.inflate(-34, -190).move(0, -80), rect.inflate(-34, -190).move(0, 85)):
        pygame.draw.rect(surf, (48, 32, 26), panel)
        pygame.draw.rect(surf, (74, 52, 42), panel, 2)
    pygame.draw.circle(surf, (170, 140, 80), (rect.right - 16, rect.centery + 10), 6)
    plate = pygame.Rect(0, 0, 38, 20)
    plate.center = (rect.centerx, rect.top + 26)
    pygame.draw.rect(surf, (150, 130, 90), plate)


def _lamp_fixture(surf, x, y=64):
    pygame.draw.line(surf, (10, 10, 12), (x, 40), (x, y), 3)
    pygame.draw.rect(surf, (200, 190, 150), pygame.Rect(x - 22, y, 44, 10), border_radius=4)


def build_corridor(loc, objects, night=0):
    w = loc.width
    surf = pygame.Surface((w, H))
    _gradient(w, 0, WALL_BOTTOM, (78, 92, 116), (48, 58, 76), surf)
    pygame.draw.rect(surf, (12, 14, 18), (0, 0, w, 60))
    for x in range(0, w, 300):
        pygame.draw.rect(surf, (18, 20, 25), (x, 0, 14, 60))
    pygame.draw.rect(surf, (30, 36, 45), (0, 390, w, WALL_BOTTOM - 390))
    pygame.draw.line(surf, (70, 80, 92), (0, 390), (w, 390), 3)
    _floor(surf, w)
    windows = []
    for x in (700, 1600):
        _window(surf, pygame.Rect(x - 90, 130, 180, 220), windows)
    lights, pillars = [], [1350]
    for x, flick, power in ((450, 0.8, 1), (1100, 0, 0), (1700, 0.35, 1), (2200, 0.1, 1)):
        _lamp_fixture(surf, x)
        if power:
            lights.append(dict(x=x, y=100, r=380, color=(255, 214, 160),
                               i=1.0, flicker=flick, seed=x))
    for o in objects:
        if o.kind == "door":
            _door(surf, o)
            if o.active(night):   # тек белсенді есіктің астынан жарық түседі
                lights.append(dict(x=o.x, y=WALL_BOTTOM - 20, r=190, color=(255, 190, 110),
                                   i=0.8, flicker=0.15, seed=o.x))
    for wnd in windows:  # терезеден түсетін суық жарық
        lights.append(dict(x=wnd.centerx, y=wnd.centery + 60, r=300,
                           color=(110, 150, 220), i=0.75, flicker=0, seed=0))
    return Scenery(surf, windows, lights, pillars, ambient=(120, 130, 168))


def _room_darkhan(surf, lights):
    pygame.draw.rect(surf, (20, 18, 24), (300, 470, 230, 90))      # кереует
    pygame.draw.rect(surf, (36, 40, 62), (306, 464, 218, 40), border_radius=6)
    pygame.draw.rect(surf, (14, 12, 16), (292, 420, 16, 140))
    pygame.draw.rect(surf, (28, 22, 20), (1010, 500, 160, 14))     # үстел мен шам
    pygame.draw.rect(surf, (20, 16, 14), (1020, 514, 12, 46))
    pygame.draw.rect(surf, (20, 16, 14), (1148, 514, 12, 46))
    pygame.draw.rect(surf, (230, 200, 120), (1080, 470, 14, 30), border_radius=3)
    for i in range(3):                                              # сөре
        pygame.draw.rect(surf, (22, 18, 18), (860, 250 + i * 58, 200, 8))
        for j in range(7):
            pygame.draw.rect(surf, [(80, 50, 46), (50, 64, 80), (90, 80, 52)][(i + j) % 3],
                             (868 + j * 26, 214 + i * 58, 18, 36))
    lights.append(dict(x=1087, y=470, r=420, color=(255, 190, 110), i=1.0, flicker=0.25, seed=3))


def _room_girls(surf, lights):
    pygame.draw.ellipse(surf, (18, 14, 14), (260, 470, 150, 110))   # барабан
    pygame.draw.ellipse(surf, (60, 64, 70), (260, 462, 150, 40))
    pygame.draw.line(surf, (30, 24, 22), (290, 560), (270, 600), 5)
    pygame.draw.line(surf, (30, 24, 22), (380, 560), (400, 600), 5)
    pygame.draw.rect(surf, (28, 22, 20), (1000, 500, 200, 14))      # тігін машинасы үстелі
    pygame.draw.rect(surf, (20, 16, 14), (1015, 514, 12, 46))
    pygame.draw.rect(surf, (20, 16, 14), (1173, 514, 12, 46))
    pygame.draw.rect(surf, (50, 52, 60), (1060, 456, 80, 44), border_radius=6)
    pygame.draw.rect(surf, (70, 72, 82), (1110, 436, 12, 24))
    pygame.draw.circle(surf, (150, 60, 90), (1075, 440), 10)         # катушка
    for i in range(4):                                               # маталар
        pygame.draw.rect(surf, [(110, 60, 90), (60, 90, 100), (100, 90, 50), (70, 60, 110)][i],
                         (860 + i * 28, 300, 22, 120))
    lights.append(dict(x=1100, y=470, r=420, color=(255, 190, 120), i=1.0, flicker=0.2, seed=5))


def _room_bekzat(surf, lights):
    pygame.draw.rect(surf, (28, 22, 20), (980, 500, 200, 14))       # үстел
    pygame.draw.rect(surf, (20, 16, 14), (995, 514, 12, 46))
    pygame.draw.rect(surf, (20, 16, 14), (1153, 514, 12, 46))
    pygame.draw.polygon(surf, (36, 28, 24), [(1060, 500), (1120, 500), (1105, 420), (1075, 420)])  # метроном
    pygame.draw.line(surf, (190, 180, 150), (1090, 500), (1100, 428), 3)
    for k in range(6):                                               # ноталар/қағаздар
        pygame.draw.rect(surf, (150, 148, 138), (860 + k * 22, 520 - (k % 2) * 6, 18, 24))
    pygame.draw.rect(surf, (20, 18, 24), (300, 470, 230, 90))        # кереует
    pygame.draw.rect(surf, (52, 40, 40), (306, 464, 218, 40), border_radius=6)
    lights.append(dict(x=1090, y=450, r=300, color=(255, 215, 150), i=0.8, flicker=0.55, seed=9))


ROOM_VARIANTS = {"darkhan_room": _room_darkhan, "girls_room": _room_girls,
                 "bekzat_room": _room_bekzat}
ROOM_AMBIENT = {"darkhan_room": (140, 124, 148), "girls_room": (142, 126, 150),
                "bekzat_room": (122, 118, 150)}


def build_room(loc, objects, night=0):
    w = loc.width
    surf = pygame.Surface((w, H))
    _gradient(w, 0, WALL_BOTTOM, (104, 84, 92), (66, 54, 64), surf)
    pygame.draw.rect(surf, (14, 12, 16), (0, 0, w, 40))
    _floor(surf, w)
    windows = []
    _window(surf, pygame.Rect(540, 120, 200, 240), windows)
    lights = [dict(x=640, y=330, r=320, color=(110, 150, 220), i=0.7, flicker=0, seed=0)]
    ROOM_VARIANTS.get(loc.id, _room_darkhan)(surf, lights)
    for o in objects:
        if o.kind == "door":
            _door(surf, o)
    return Scenery(surf, windows, lights, [], ambient=ROOM_AMBIENT.get(loc.id, (140, 124, 148)))


def build_scenery(loc, night=0):
    builder = build_corridor if loc.id == "corridor" else build_room
    return builder(loc, loc.objects, night)
