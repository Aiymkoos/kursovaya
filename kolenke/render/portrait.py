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
BODY = (10, 10, 16)
RIM_DIM = {"human": 0.9, "fading": 0.5, "shadow": 0.7}
CHARACTERS = {
    "darkhan": (240, 160, 60),
    "zhanel": (90, 215, 190),
    "madina": (215, 125, 225),
    "bekzat": (245, 220, 125),
    "me": (120, 180, 240),
}
# Кейіпкер келбеті: тері, шаш, киім, шаш үлгісі
LOOK = {
    "darkhan": dict(skin=(236, 192, 152), hair=(46, 30, 24), cloth=(214, 204, 192), cloth2=(160, 148, 138), style="hat"),
    "zhanel": dict(skin=(228, 182, 146), hair=(24, 22, 30), cloth=(52, 108, 110), cloth2=(34, 76, 80), style="long"),
    "madina": dict(skin=(238, 198, 168), hair=(70, 40, 34), cloth=(132, 78, 142), cloth2=(96, 54, 106), style="bun"),
    "bekzat": dict(skin=(220, 178, 142), hair=(30, 24, 26), cloth=(226, 218, 196), cloth2=(52, 56, 78), style="messy"),
    "me": dict(skin=(230, 188, 152), hair=(54, 38, 32), cloth=(66, 98, 150), cloth2=(44, 68, 108), style="short"),
}
_cache = {}
_glow_cache = {}


def _mix(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _lerp(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


class _Pen:
    """Күйге қарай түсті өзгертетін қылқалам: human — толық түс, fading — сөніп бара жатқан,
    shadow — таза қара."""

    def __init__(self, surf, state):
        self.s, self.state = surf, state

    def c(self, col):
        if self.state == "human":
            return col
        if self.state == "fading":
            g = sum(col) // 3
            return _lerp(_lerp(col, (g, g, g), 0.7), (14, 14, 22), 0.55)
        return BODY

    def ellipse(self, col, rect, width=0):
        pygame.draw.ellipse(self.s, self.c(col), tuple(int(v * S) for v in rect), width * S)

    def poly(self, col, pts):
        pygame.draw.polygon(self.s, self.c(col), [(int(x * S), int(y * S)) for x, y in pts])

    def rect(self, col, rect, radius=0):
        pygame.draw.rect(self.s, self.c(col), tuple(int(v * S) for v in rect), border_radius=radius * S)

    def circle(self, col, pos, r, width=0):
        pygame.draw.circle(self.s, self.c(col), (int(pos[0] * S), int(pos[1] * S)), int(r * S), width * S)

    def line(self, col, a, b, w=2):
        pygame.draw.line(self.s, self.c(col), (int(a[0] * S), int(a[1] * S)),
                         (int(b[0] * S), int(b[1] * S)), max(1, int(w * S)))


CX = W // 2


def _torso(p, look, accent, dx=0):
    cloth, cloth2 = look["cloth"], look["cloth2"]
    body = [(CX - 120 + dx, 405), (CX + 120 + dx, 405), (CX + 300 + dx, 520), (CX + 345 + dx, H),
            (CX - 345 + dx, H), (CX - 300 + dx, 520)]
    p.poly(cloth2, body)
    for sx in (-1, 1):
        p.circle(cloth2, (CX + sx * 262 + dx, 545), 92)
    # жарық жағы (сол жақ) — ашығырақ
    p.poly(cloth, [(CX - 118 + dx, 405), (CX + 30 + dx, 405), (CX + 40 + dx, H), (CX - 345 + dx, H),
                   (CX - 300 + dx, 520)])
    p.circle(cloth, (CX - 262 + dx, 545), 90)
    # мойын + көлеңке
    p.rect(look["skin"], (CX - 38 + dx, 330, 76, 100))


def _neck_shadow(p, look):
    p.ellipse(_mix(look["skin"], 0.72), (CX - 44, 376, 88, 56))
    p.rect(look["skin"], (CX - 38, 330, 40, 60))


def _hair_back(p, look):
    st, hc = look["style"], look["hair"]
    if st == "long":
        p.poly(hc, [(CX - 112, 220), (CX + 112, 220), (CX + 150, 520), (CX + 60, 560), (CX - 60, 560),
                    (CX - 150, 520)])
        p.ellipse(hc, (CX - 112, 120, 224, 240))
    elif st == "bun":
        p.circle(hc, (CX, 96), 52)
        p.circle(_mix(hc, 1.25), (CX - 12, 86), 22)
    elif st == "short":
        p.ellipse(hc, (CX - 104, 134, 208, 150))
    elif st == "messy":
        p.ellipse(hc, (CX - 106, 128, 212, 160))


def _head(p, look):
    skin = look["skin"]
    p.ellipse(_mix(skin, 0.8), (CX - 94, 150, 188, 232))              # көлеңкелі бет негізі
    p.ellipse(skin, (CX - 94, 150, 168, 232))                           # жарық жағы
    for sx in (-1, 1):                                                  # құлақтар
        p.ellipse(_mix(skin, 0.9 if sx < 0 else 0.72), (CX + sx * 92 - 14, 262, 28, 50))
    p.ellipse(_mix(skin, 1.04), (CX - 22, 276, 44, 58))                # мұрын көпірі


def _hair_front(p, look):
    st, hc = look["style"], look["hair"]
    hi = _mix(hc, 1.7)
    if st == "hat":
        p.rect((246, 244, 236), (CX - 104, 120, 208, 62), 10)           # қалпақ белдігі
        p.ellipse((250, 248, 240), (CX - 126, 30, 252, 130))             # қалпақ төбесі
        p.ellipse((226, 222, 212), (CX - 60, 52, 190, 96))
        p.ellipse((250, 248, 240), (CX - 126, 36, 160, 120))
        p.rect((208, 200, 188), (CX - 104, 168, 208, 12), 6)
        p.poly(hc, [(CX - 92, 186), (CX - 58, 176), (CX - 80, 232)])    # самай
        p.poly(hc, [(CX + 92, 186), (CX + 58, 176), (CX + 80, 232)])
    elif st == "long":
        p.ellipse(hc, (CX - 104, 130, 208, 120))
        p.poly(hc, [(CX - 100, 200), (CX - 20, 178), (CX + 80, 190), (CX + 100, 250), (CX + 60, 214),
                    (CX - 30, 200), (CX - 90, 256)])
        p.line(hi, (CX - 60, 150), (CX - 20, 142), 6)
    elif st == "bun":
        p.ellipse(hc, (CX - 102, 132, 204, 120))
        p.poly(hc, [(CX - 98, 204), (CX - 10, 170), (CX + 98, 204), (CX + 70, 214), (CX, 190), (CX - 70, 220)])
        p.line(hi, (CX - 54, 150), (CX - 10, 142), 6)
    elif st == "short":
        p.ellipse(hc, (CX - 104, 130, 208, 114))
        p.poly(hc, [(CX - 100, 190), (CX - 30, 160), (CX + 60, 168), (CX + 102, 200), (CX + 70, 196),
                    (CX + 10, 180), (CX - 60, 196)])
        p.line(hi, (CX - 62, 146), (CX - 16, 138), 6)
    else:  # messy
        p.ellipse(hc, (CX - 106, 124, 212, 120))
        for i, ox in enumerate((-90, -46, 0, 46, 90)):
            p.poly(hc, [(CX + ox - 26, 160), (CX + ox + 6, 108 - (i % 2) * 14), (CX + ox + 34, 166)])
        p.poly(hc, [(CX - 100, 196), (CX - 20, 170), (CX + 100, 200), (CX + 40, 190), (CX - 70, 216)])
        p.line(hi, (CX - 52, 140), (CX - 6, 124), 6)


def _face(p, look, accent, name):
    """Бет белгілері: қас, көз (ақ + нұрлы мөлдір), мұрын, ауыз, ұялу."""
    skin = look["skin"]
    brow = _mix(look["hair"], 1.1)
    for sx in (-1, 1):
        ex = CX + sx * 40
        p.ellipse(_mix(skin, 0.86), (ex - 24, 247, 48, 30))              # қабақ көлеңкесі
        p.ellipse((250, 250, 252), (ex - 19, 250, 38, 24))                # көз қарашығы ақ
        p.circle(_mix(accent, 0.75), (ex + sx * -1, 262), 11)             # нұрлы
        p.circle((12, 12, 18), (ex + sx * -1, 262), 6)
        p.circle((255, 255, 255), (ex - 4, 258), 3)
        p.line((20, 16, 20), (ex - 20, 255), (ex + 20, 253), 3)           # кірпік
        p.line(brow, (ex - sx * 20, 230), (ex + sx * 26, 224 + (4 if sx > 0 else 0)), 6)
        p.ellipse(_lerp(skin, (240, 130, 120), 0.35), (ex - 18, 296, 36, 20))   # ұялу
    p.line(_mix(skin, 0.6), (CX - 4, 286), (CX - 10, 304), 3)
    p.line(_mix(skin, 0.6), (CX - 10, 304), (CX + 2, 308), 3)
    p.line((150, 70, 70), (CX - 24, 332), (CX + 24, 332), 4)
    p.line((150, 70, 70), (CX - 24, 332), (CX - 30, 326), 3)
    p.line((150, 70, 70), (CX + 24, 332), (CX + 30, 328), 3)


def _outfit(p, look, accent, name):
    """Киім бөлшектері мен кейіпкерге тән аксессуар."""
    cloth2 = look["cloth2"]
    if name == "darkhan":                                      # наубайшы алжапқышы + бау
        p.poly(accent, [(CX - 70, 430), (CX + 70, 430), (CX + 90, H), (CX - 90, H)])
        p.poly(_mix(accent, 0.7), [(CX + 20, 430), (CX + 70, 430), (CX + 90, H), (CX + 40, H)])
        p.line((240, 232, 222), (CX - 70, 430), (CX - 30, 405), 10)
        p.line((240, 232, 222), (CX + 70, 430), (CX + 30, 405), 10)
        for i in range(6):                                     # ұн дақтары
            p.circle((246, 244, 238), (CX - 190 + i * 38, 520 + (i * 37) % 60), 5 + i % 3)
    elif name == "zhanel":                                     # құлаққап + капюшон бауы
        p.line((26, 28, 36), (CX - 112, 220), (CX - 98, 150), 14)
        pygame.draw.arc(p.s, p.c((26, 28, 36)), (int((CX - 120) * S), int(70 * S), int(240 * S), int(250 * S)),
                        0.15, math.pi - 0.15, 14 * S)
        for sx in (-1, 1):
            p.ellipse((30, 32, 42), (CX + sx * 112 - 26, 232, 52, 86))
            p.ellipse(accent, (CX + sx * 112 - 26, 232, 52, 86), 4)
            p.line(accent, (CX + sx * 62, 410), (CX + sx * 70, 520), 5)
        p.circle(accent, (CX + 330, 340), 9)
        p.line((40, 40, 50), (CX + 200, 520), (CX + 330, 340), 8)
    elif name == "madina":                                     # кардиган + өлшеу таспасы
        p.poly(look["cloth"], [(CX - 60, 410), (CX + 60, 410), (CX + 36, H), (CX - 36, H)])
        for sx in (-1, 1):
            p.line(accent, (CX + sx * 34, 408), (CX + sx * 76, H), 10)
        p.line(accent, (CX - 40, 414), (CX + 40, 414), 9)
        for k in range(9):
            p.line((245, 240, 230), (CX - 62 + k * 15, 420 + k * 0), (CX - 62 + k * 15, 432), 2)
        p.circle((240, 220, 150), (CX + 12, 560), 7)           # түйме
        p.circle((240, 220, 150), (CX + 12, 610), 7)
    elif name == "bekzat":                                     # жилет + галстук + көзәйнек
        p.poly(cloth2, [(CX - 70, 410), (CX, 520), (CX - 14, H), (CX - 118, H), (CX - 150, 470)])
        p.poly(cloth2, [(CX + 70, 410), (CX, 520), (CX + 14, H), (CX + 118, H), (CX + 150, 470)])
        p.poly((238, 232, 214), [(CX - 40, 408), (CX, 470), (CX + 40, 408)])
        p.poly(accent, [(CX - 14, 440), (CX + 14, 440), (CX + 22, 560), (CX, 590), (CX - 22, 560)])
        for sx in (-1, 1):
            p.circle((34, 34, 46), (CX + sx * 42, 262), 36, 5)
        p.line((34, 34, 46), (CX - 8, 262), (CX + 8, 262), 5)
        p.line(accent, (CX - 20, 244), (CX - 6, 232), 4)
    else:                                                      # me: мойынорағыш
        p.rect(accent, (CX - 74, 396, 148, 44), 18)
        p.rect(_mix(accent, 0.8), (CX - 74, 416, 148, 24), 12)
        p.poly(accent, [(CX + 28, 430), (CX + 106, 430), (CX + 124, 640), (CX + 62, 612)])
        p.line(_mix(accent, 0.7), (CX + 60, 450), (CX + 86, 620), 3)
        for sx in (-1, 1):                                     # жаға
            p.poly(cloth2, [(CX + sx * 74, 405), (CX + sx * 150, 430), (CX + sx * 90, 470)])


def _folds(p, look):
    """Киім қыртыстары — көлемдік әсер."""
    dark = _mix(look["cloth2"], 0.7)
    for x0, x1 in ((-230, -200), (-160, -150), (180, 210), (250, 290)):
        p.line(dark, (CX + x0, 520), (CX + x1, H), 4)


def _erode(surf, amount, seed):
    """Шеттері бұзылу: кездейсоқ дөңгелектермен альфаны азайту."""
    rng = random.Random(seed)
    mask = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for _ in range(int(70 * amount)):
        x = rng.randint(0, W * S)
        y = rng.randint(30 * S, H * S)
        if rng.random() < 0.65:   # көбіне шетке жақын
            x = W * S // 2 + rng.choice((-1, 1)) * rng.randint(70 * S, 340 * S)
        pygame.draw.circle(mask, (255, 255, 255, 255), (x, y), rng.randint(8 * S, 34 * S))
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)


def _draw_character(surf, name, state, accent, dx=0, dy=0):
    look = LOOK[name]
    p = _Pen(surf, state)
    _hair_back(p, look)
    _torso(p, look, accent, dx)
    if state != "shadow":
        _folds(p, look)
    _head(p, look)
    _neck_shadow(p, look)
    _hair_front(p, look)
    if state == "human":
        _face(p, look, accent, name)
    elif state == "fading":
        ex = CX - 40
        p.ellipse(_mix(accent, 0.5), (ex - 14, 252, 28, 18))        # бір көз ғана солғын
    _outfit(p, look, accent, name)


def build_portrait(name, state):
    """Портрет бетін жасайды (кэштеледі). Қайтарады: W×H SRCALPHA."""
    key = (name, state)
    if key in _cache:
        return _cache[key]
    accent = CHARACTERS[name]
    big = pygame.Surface((W * S, H * S), pygame.SRCALPHA)
    # контр-жарық жиегі: бейненің жылжытылған көшірмесі акцент түсімен
    rim = pygame.Surface((W * S, H * S), pygame.SRCALPHA)
    _draw_character(rim, name, "shadow", accent)
    mask = pygame.mask.from_surface(rim)
    rim_col = _mix(accent, RIM_DIM[state])
    rim_img = mask.to_surface(setcolor=rim_col + (255,), unsetcolor=(0, 0, 0, 0))
    big.blit(rim_img, (8 * S, -3 * S))
    _draw_character(big, name, state, accent)
    if state == "human":                    # сол жақтан жарық: оң жақты көлеңкелеу
        grad = pygame.Surface((W * S, 1))
        for x in range(W * S):
            k = x / (W * S)
            v = int(255 - 70 * max(0.0, k - 0.35) / 0.65)
            grad.set_at((x, 0), (v, v, v))
        big.blit(pygame.transform.scale(grad, (W * S, H * S)), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    if state == "fading":
        _erode(big, 1.0, seed=hash(name) & 0xFFFF)
    elif state == "shadow":
        _erode(big, 0.25, seed=(hash(name) + 1) & 0xFFFF)
    surf = pygame.transform.smoothscale(big, (W, H))
    _cache[key] = surf
    return surf


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
