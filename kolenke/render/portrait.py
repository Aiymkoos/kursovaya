"""Диалогтағы үлкен силуэт-портреттер: жұмсартылған пішін, контр-жарық, 3 күй.

Күйлер (көлеңке жұтқан сайын детальдар жоғалады — ТЗ):
  human  — бет белгілері, киім бөлшектері, акцент жарқырайды;
  fading — белгілер өшеді, шеті бұзылады, акцент солғын;
  shadow — таза қара силуэт, тек жұқа акцентті жиек.
Портрет 2x масштабта сызылып, кішірейтіледі (anti-aliasing) және кэштеледі.
"""
import math
import random

import pygame

W, H = 520, 700            # соңғы өлшем
S = 2                      # супер-семплинг
BODY = (7, 7, 11)
RIM_DIM = {"human": 0.75, "fading": 0.4, "shadow": 0.55}
STATE_DETAIL = {"human": 1.0, "fading": 0.45, "shadow": 0.0}
CHARACTERS = {
    "darkhan": (230, 150, 50),
    "zhanel": (90, 210, 180),
    "madina": (205, 120, 215),
    "bekzat": (240, 215, 120),
    "me": (110, 170, 230),
}
_cache = {}
_glow_cache = {}


def _mix(c, k):
    return tuple(int(v * k) for v in c)


def _shape(surf, color, dx=0, dy=0, name="me"):
    """Дене пішіні: бас, мойын, иықтар, кеуде. 2x координатада."""
    cx = W * S // 2 + dx
    top = dy
    pygame.draw.polygon(surf, color, [
        (cx - 110 * S // 1, top + 410 * S // 1 - 0),
        (cx + 110 * S, top + 410 * S),
        (cx + 310 * S, top + 560 * S), (cx + 340 * S, top + H * S),
        (cx - 340 * S, top + H * S), (cx - 310 * S, top + 560 * S)])
    for sx in (-1, 1):                                   # дөңгелек иықтар
        pygame.draw.circle(surf, color, (cx + sx * 255 * S, top + 565 * S), 90 * S)
    pygame.draw.rect(surf, color, (cx - 34 * S, top + 330 * S, 68 * S, 100 * S))
    pygame.draw.ellipse(surf, color, (cx - 96 * S, top + 130 * S, 192 * S, 236 * S))


def _features(surf, name, accent, detail):
    """Кейіпкерге тән бөлшектер (бас киім, құлаққап, лента, көзәйнек…)."""
    cx = W * S // 2
    dark2 = (16, 16, 24)
    ac = _mix(accent, 0.35 + 0.65 * detail) if detail > 0 else None
    if name == "darkhan":                                     # наубайшы қалпағы + алжапқыш бауы
        pygame.draw.ellipse(surf, BODY, (cx - 118 * S, 66 * S, 236 * S, 120 * S))
        pygame.draw.rect(surf, dark2, (cx - 100 * S, 168 * S, 200 * S, 20 * S), border_radius=8)
        if ac:
            pygame.draw.polygon(surf, ac, [(cx - 150 * S, 470 * S), (cx - 118 * S, 470 * S),
                                           (cx + 250 * S, H * S), (cx + 200 * S, H * S)])
    elif name == "zhanel":                                    # құлаққап + таяқ ұшы
        pygame.draw.arc(surf, BODY, (cx - 118 * S, 70 * S, 236 * S, 260 * S), 0.1, math.pi - 0.1, 14 * S)
        for sx in (-1, 1):
            pygame.draw.ellipse(surf, dark2, (cx + sx * 112 * S - 26 * S, 236 * S, 52 * S, 84 * S))
            if ac:
                pygame.draw.ellipse(surf, ac, (cx + sx * 112 * S - 26 * S, 236 * S, 52 * S, 84 * S), 4 * S)
        pygame.draw.line(surf, BODY, (cx + 200 * S, 520 * S), (cx + 330 * S, 340 * S), 10 * S)
        if ac:
            pygame.draw.circle(surf, ac, (cx + 330 * S, 340 * S), 9 * S)
    elif name == "madina":                                    # шаш түйіні + өлшеу таспасы
        pygame.draw.circle(surf, BODY, (cx, 96 * S), 50 * S)
        if ac:
            for sx in (-1, 1):
                pygame.draw.line(surf, ac, (cx + sx * 30 * S, 400 * S), (cx + sx * 70 * S, H * S), 7 * S)
            pygame.draw.line(surf, ac, (cx - 36 * S, 410 * S), (cx + 36 * S, 410 * S), 7 * S)
    elif name == "bekzat":                                    # көзәйнек + жағасы
        for sx in (-1, 1):
            pygame.draw.circle(surf, dark2, (cx + sx * 44 * S, 250 * S), 36 * S, 5 * S)
            if ac:
                pygame.draw.line(surf, ac, (cx + sx * 44 * S - 18 * S, 238 * S),
                                 (cx + sx * 44 * S - 4 * S, 228 * S), 4 * S)
        pygame.draw.line(surf, dark2, (cx - 8 * S, 250 * S), (cx + 8 * S, 250 * S), 4 * S)
        pygame.draw.polygon(surf, dark2, [(cx - 60 * S, 410 * S), (cx, 500 * S), (cx - 12 * S, 560 * S)])
        pygame.draw.polygon(surf, dark2, [(cx + 60 * S, 410 * S), (cx, 500 * S), (cx + 12 * S, 560 * S)])
    else:                                                     # me: мойынорағыш
        if ac:
            pygame.draw.rect(surf, ac, (cx - 70 * S, 400 * S, 140 * S, 38 * S), border_radius=14 * S)
            pygame.draw.polygon(surf, ac, [(cx + 30 * S, 430 * S), (cx + 100 * S, 430 * S),
                                           (cx + 120 * S, 620 * S), (cx + 60 * S, 600 * S)])
    if detail >= 0.9:                                         # бет: көз, қас, ауыз
        for sx in (-1, 1):
            if name != "bekzat":
                pygame.draw.ellipse(surf, accent, (cx + sx * 40 * S - 9 * S, 252 * S, 18 * S, 12 * S))
            pygame.draw.line(surf, dark2, (cx + sx * 66 * S, 226 * S), (cx + sx * 20 * S, 220 * S), 4 * S)
        pygame.draw.line(surf, (24, 24, 34), (cx - 28 * S, 318 * S), (cx + 28 * S, 318 * S), 4 * S)
        pygame.draw.line(surf, (24, 24, 34), (cx, 262 * S), (cx - 6 * S, 300 * S), 3 * S)
    elif detail > 0.2:                                        # fading: бір көз ғана солғын
        pygame.draw.ellipse(surf, _mix(accent, 0.4), (cx - 49 * S, 252 * S, 18 * S, 12 * S))


def _erode(surf, amount, seed):
    """Шеттері бұзылу: кездейсоқ дөңгелектермен альфаны азайту."""
    rng = random.Random(seed)
    mask = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    n = int(70 * amount)
    for _ in range(n):
        side = rng.random()
        x = rng.randint(0, W * S)
        y = rng.randint(30 * S, H * S)
        if side < 0.65:   # көбіне шетке жақын
            x = W * S // 2 + rng.choice((-1, 1)) * rng.randint(70 * S, 340 * S)
        pygame.draw.circle(mask, (255, 255, 255, 255), (x, y), rng.randint(8 * S, 34 * S))
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)


def build_portrait(name, state):
    """Портрет бетін жасайды (кэштеледі). Қайтарады: W×H SRCALPHA."""
    key = (name, state)
    if key in _cache:
        return _cache[key]
    accent = CHARACTERS[name]
    detail = STATE_DETAIL[state]
    big = pygame.Surface((W * S, H * S), pygame.SRCALPHA)
    rim = _mix(accent, RIM_DIM[state])
    _shape(big, rim, dx=7 * S, dy=-3 * S)           # контр-жарық жиегі
    _shape(big, BODY)
    if state != "shadow":
        _features(big, name, accent, detail)
    else:
        _features_shadow(big, name)
    if state == "fading":
        _erode(big, 1.0, seed=hash(name) & 0xFFFF)
    elif state == "shadow":
        _erode(big, 0.25, seed=(hash(name) + 1) & 0xFFFF)
    surf = pygame.transform.smoothscale(big, (W, H))
    _cache[key] = surf
    return surf


def _features_shadow(surf, name):
    """Көлеңке күйі: тек бас киім/аксессуар пішіні (қара), акцент жоқ."""
    _features(surf, name, (0, 0, 0), 0.0)


def glow(accent, radius, strength=1.0):
    key = (accent, radius, int(strength * 10))
    if key not in _glow_cache:
        base = pygame.Surface((64, 64))
        for i in range(32, 0, -1):
            f = (1 - i / 32) ** 2 * strength * 0.55
            pygame.draw.circle(base, _mix(accent, f), (32, 32), i)
        _glow_cache[key] = pygame.transform.smoothscale(base, (radius * 2, radius * 2))
    return _glow_cache[key]


def draw_portrait(surface, name, state, cx, bottom, t, active=True, scale=1.0):
    """Портретті экранға салу: артқы жарқыл + тыныс алу қозғалысы.

    cx — ортасы, bottom — төменгі шеті. active=False болса күңгірттеледі."""
    img = build_portrait(name, state)
    accent = CHARACTERS[name]
    breathe = math.sin(t * 1.8 + hash(name) % 7) * 4
    w, h = int(W * scale), int(H * scale)
    if scale != 1.0:
        img = pygame.transform.smoothscale(img, (w, h))
    pos = img.get_rect(midbottom=(cx, bottom + breathe))
    g = glow(accent, int(330 * scale), 0.9 if state == "human" else 0.55 if state == "fading" else 0.3)
    surface.blit(g, g.get_rect(center=(cx, pos.top + 220 * scale)), special_flags=pygame.BLEND_RGB_ADD)
    surface.blit(img, pos)
    if not active:
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        surface.blit(dim, pos, special_flags=0)
    return pos
