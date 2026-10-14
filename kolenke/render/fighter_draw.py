"""Жауынгерді күйі мен кадрына қарай сызу (поза — moves.json ішіндегі 'arm' кілттері)."""
import math

import pygame

from kolenke.combat.hitbox import GROUND
from kolenke.render.silhouette import draw_silhouette
from kolenke.render.sprite import figure, has_sprite

SPRITE_NAME = {"player": "me"}         # Fight-та ойыншының аты «player», ал сурет — me.png
FIGHT_HEIGHT = 330                     # жекпе-жектегі бойы (пиксель)

FLASH_COLOR = (235, 235, 248)


def _lerp(a, b, t):
    return a + (b - a) * t


def pose(f):
    """(arm_angle, lean, weapon_len) — жауынгердің қазіргі позасы."""
    weapon = 28.0 if f.spec.get("weapon") else 0.0
    base_arm = 0.45 if weapon else None
    s = f.state
    m = f.move
    if m:
        a0, a1, a2, a3 = m["arm"]
        su, ac, rec = m["startup"], m["active"], m["recovery"]
        lean_wind = m.get("lean", -8)
        weapon = m.get("weapon_len", weapon)
        if f.frame < su:
            t = f.frame / su
            t = t * t * (3 - 2 * t)      # ease: қозғалыс «дайындалады»
            return _lerp(a0, a1, t), lean_wind * t, weapon
        if f.frame < su + ac:
            return a2, 14.0, weapon
        t = (f.frame - su - ac) / max(1, rec)
        return _lerp(a2, a3, t), 14.0 * (1 - t), weapon
    if s == "block":
        return 2.3, -4.0, weapon
    if s == "hurt":
        return base_arm, -16.0, weapon
    if s == "stagger":
        return 0.2, -22.0, weapon
    if s == "dead":
        return base_arm, -48.0, 0.0
    return base_arm, 0.0, weapon


def draw_fighter(surface, f, accent, t, part="all", detail=1.0):
    """Қайтарады: (қол, ұш) — соққы ізі (trail) үшін."""
    arm, lean, weapon = pose(f)
    lean += math.sin(t * 2.2 + (0 if f.facing > 0 else 1.3)) * 1.5
    swing = math.sin(f.walk_phase * 2) * 0.8 if f.walking else 0.0
    return draw_silhouette(
        surface, f.x, GROUND, accent, f.facing, swing, t=t, part=part,
        detail=0.0 if f.state == "dead" else detail,
        arm_angle=arm, lean=lean, weapon=weapon,
        body_color=FLASH_COLOR if f.flash > 0 else None)


def _rotated_on_feet(img, angle_deg, foot):
    """Суретті табанының ортасынан бұрады: табан нүктесі (foot) орнында қалады."""
    w, h = img.get_size()
    rot = pygame.transform.rotate(img, angle_deg)
    a = math.radians(angle_deg)
    off_x, off_y = (h / 2) * math.sin(a), (h / 2) * math.cos(a)     # центрден табанға вектор, бұрылғаннан кейін
    rect = rot.get_rect(center=(foot[0] - off_x, foot[1] - off_y))
    return rot, rect


def sprite_name(f):
    return SPRITE_NAME.get(f.name, f.name)


def has_fighter_sprite(f):
    return has_sprite(sprite_name(f))


def draw_fighter_sprite(surface, f, t, detail=1.0):
    """Жауынгерді дайын сурет ретінде сызу: еңкею, ілгері серпілу, соққы жарқылы, құлау.

    Қайтарады: (қол, ұш) — соққы ізі үшін (силуэттегі сияқты)."""
    arm, lean, weapon = pose(f)
    lean += math.sin(t * 2.2 + (0 if f.facing > 0 else 1.3)) * 1.5
    dead = f.state == "dead"
    img = figure(sprite_name(f), f.facing, 0.0 if dead else detail, FIGHT_HEIGHT)
    if f.flash > 0 and not dead:                                  # соққы вспышкасы: ақ жарқыл
        img = img.copy()
        img.fill((150, 150, 160, 0), special_flags=pygame.BLEND_RGB_ADD)
    angle = -lean * f.facing * 0.55                               # ілгері еңкею (оңға қараса — сағат тілімен)
    lunge = f.facing * 18 if (f.move and f.phase == "active") else 0
    x = f.x + lunge
    swing = math.sin(f.walk_phase * 2) if f.walking else 0.0
    bob = abs(swing) * 6
    if dead:
        angle = 78 * f.facing                                     # артына жығылады
    rot, rect = _rotated_on_feet(img, angle, (x, GROUND + 4 - bob))
    sh = pygame.Surface((int(FIGHT_HEIGHT * 0.45), 22), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 120), sh.get_rect())
    surface.blit(sh, sh.get_rect(center=(f.x, GROUND + 4)))
    surface.blit(rot, rect)
    if f.move and f.phase == "active":
        hand = (x + f.facing * 48, GROUND - FIGHT_HEIGHT * 0.52)
        reach = 58 + weapon + abs(math.sin(arm)) * 30
        return hand, (hand[0] + f.facing * reach, hand[1] + math.cos(arm) * 22)
    return None
