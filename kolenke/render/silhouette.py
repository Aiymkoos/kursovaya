"""Силуэт + бір акцентті түс: кейіпкерлерді код арқылы сызу.

Дене қара, акцент (мойынорағыш пен көз) — жарықтан тыс «жарқырайды».
detail 1.0 → толық, 0.0 → детальсіз қара дақ (көлеңке жұтқанда азаяды).
arm_angle: алдыңғы қолдың бұрышы (0 — төмен, π/2 — алға, π — жоғары).
"""
import math

import pygame

BODY = (5, 5, 8)
STEEL = (150, 156, 168)
_shadow_cache = {}


def _shadow(width):
    key = int(width)
    if key not in _shadow_cache:
        surf = pygame.Surface((key, max(6, key // 5)), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 110), surf.get_rect())
        _shadow_cache[key] = surf
    return _shadow_cache[key]


def draw_silhouette(surface, x, ground_y, accent, facing=1, swing=0.0,
                    scale=1.0, detail=1.0, t=0.0, part="all",
                    arm_angle=None, lean=0.0, weapon=0.0, body_color=None):
    """part: "body" (жарықтандыруға дейін), "accent" (кейін, эмиссия), "all".

    Қайтарады: (қол, пышақ ұшы) нүктелері — тек body кезінде және arm_angle берілсе.
    """
    s = scale
    col = body_color or BODY
    hip_y = ground_y - 82 * s
    shoulder_y = ground_y - 142 * s
    head_y = ground_y - 162 * s
    lx = lean * s                       # денені еңкейту (алға оң)
    hx = x + facing * lx                # бас/иық орны
    sx = x + facing * lx * 0.5
    reach = None
    if part in ("body", "all"):
        sh = _shadow(70 * s)
        surface.blit(sh, sh.get_rect(center=(x, ground_y + 2)))
        for side in (-1, 1):  # аяқтар
            lift = max(0.0, swing * side) * 7 * s
            foot = (x + side * 7 * s + swing * side * 20 * s, ground_y - lift)
            pygame.draw.line(surface, col, (x + side * 7 * s, hip_y), foot,
                             max(1, int(10 * s)))
        pygame.draw.polygon(surface, col, [  # пальто
            (sx - 19 * s, shoulder_y), (sx + 19 * s, shoulder_y),
            (x + 25 * s, hip_y + 14 * s), (x - 25 * s, hip_y + 14 * s)])
        for side in (-1, 1):  # қолдар
            shoulder = (sx + side * 18 * s, shoulder_y + 4 * s)
            if arm_angle is not None and side == facing:
                d = (facing * math.sin(arm_angle), math.cos(arm_angle))
                hand = (shoulder[0] + d[0] * 52 * s, shoulder[1] + d[1] * 52 * s)
                pygame.draw.line(surface, col, shoulder, hand, max(1, int(8 * s)))
                tip = hand
                if weapon:
                    tip = (hand[0] + d[0] * weapon * s, hand[1] + d[1] * weapon * s)
                    pygame.draw.line(surface, STEEL if not body_color else col,
                                     hand, tip, max(1, int(4 * s)))
                reach = (hand, tip)
            else:
                hand = (x + side * 22 * s - swing * side * 12 * s, shoulder_y + 52 * s)
                pygame.draw.line(surface, col, shoulder, hand, max(1, int(8 * s)))
        pygame.draw.line(surface, col, (sx, shoulder_y), (hx, head_y), int(9 * s))
        pygame.draw.circle(surface, col, (int(hx), int(head_y)), max(2, int(15 * s)))
    if part in ("accent", "all") and detail > 0:
        c = tuple(int(BODY[i] + (accent[i] - BODY[i]) * detail) for i in range(3))
        neck_y = shoulder_y - 3 * s
        pygame.draw.rect(surface, c, pygame.Rect(sx - 14 * s, neck_y - 3 * s,
                                                 28 * s, 8 * s), border_radius=int(3 * s))
        wave = math.sin(t * 6) * 5 * s
        tx = sx - facing * 12 * s
        pygame.draw.polygon(surface, c, [
            (tx, neck_y), (tx + facing * 4 * s, neck_y + 4 * s),
            (tx - facing * 30 * s, neck_y + 10 * s + wave),
            (tx - facing * 30 * s, neck_y + 2 * s + wave)])
        if detail > 0.6:  # көз
            pygame.draw.circle(surface, c, (int(hx + facing * 6 * s),
                                            int(head_y - 2 * s)), max(1, int(2 * s)))
    return reach
