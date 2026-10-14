"""Толық бойлы спрайттар (assets/sprites/<аты>.png): жүру сахнасындағы кейіпкерлер.

Сурет оңға қарап тұрады; солға қараса айналдырылады. Файл жоқ болса — draw_sprite False қайтарады,
сонда сахна кодпен сызылған силуэтті қолданады.
"""
import math

import pygame

from kolenke.core.assets import load_image

SPRITE_H = 215          # экрандағы биіктік (пиксель)
ALPHA_CUT = 40          # осы мәннен төмен альфа — қоқыс, кесу кезінде ескерілмейді
_base = {}              # аты -> (оңға қараған масштабталған бет) немесе None
_tinted = {}            # (аты, бағыт, жарықтық деңгейі) -> бет
_shadows = {}


def _crop_to_figure(img):
    rects = pygame.mask.from_surface(img, ALPHA_CUT).get_bounding_rects()
    if not rects:
        return img
    box = rects[0].unionall(rects[1:])
    return img.subsurface(box).copy()


def get_sprite(name):
    """Масштабталған спрайт (оңға қарайды) немесе None."""
    if name not in _base:
        img = load_image(f"sprites/{name}")
        if img is None:
            _base[name] = None
        else:
            img = _crop_to_figure(img)
            k = SPRITE_H / img.get_height()
            size = (max(1, round(img.get_width() * k)), SPRITE_H)
            _base[name] = pygame.transform.smoothscale(img, size)
    return _base[name]


def has_sprite(name):
    return get_sprite(name) is not None


def _variant(name, facing, detail):
    """Бағыты мен «жұтылу» деңгейіне сай бет (кэштеледі). detail 1.0 — толық түс, 0 — қара."""
    level = round(max(0.0, min(1.0, detail)) * 6)
    key = (name, facing, level)
    if key not in _tinted:
        img = get_sprite(name)
        if facing < 0:
            img = pygame.transform.flip(img, True, False)
        if level < 6:
            img = img.copy()
            k = int(255 * (0.15 + 0.85 * level / 6))
            img.fill((k, k, k, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _tinted[key] = img
    return _tinted[key]


def figure(name, facing=1, detail=1.0, height=None):
    """Дайын бет (бағыты мен күңгірттенуі ескеріледі); height берілсе — сол биіктікке масштабталады."""
    img = _variant(name, facing, detail)
    if height and height != img.get_height():
        img = pygame.transform.smoothscale(
            img, (max(1, round(img.get_width() * height / img.get_height())), int(height)))
    return img


def _shadow(width):
    key = int(width)
    if key not in _shadows:
        surf = pygame.Surface((key, max(6, key // 5)), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 110), surf.get_rect())
        _shadows[key] = surf
    return _shadows[key]


def draw_sprite(surface, name, x, ground_y, facing=1, swing=0.0, t=0.0, detail=1.0, scale=1.0):
    """Спрайтты табанын ground_y-ге қойып сызады. Жүргенде жеңіл секіреді, тұрғанда тыныс алады.

    Қайтарады: True — сурет бар және сызылды; False — файл жоқ (силуэт сызу керек)."""
    if get_sprite(name) is None:
        return False
    img = _variant(name, facing, detail)
    moving = abs(swing) > 0.02
    bob = abs(swing) * 5 if moving else 0.0                    # қадам кезінде жоғары-төмен
    breathe = 1.0 + 0.012 * math.sin(t * 2.0 + len(name))      # тынық күйде жеңіл тыныс
    h = int(img.get_height() * scale * (1.0 if moving else breathe))
    if h != img.get_height():
        img = pygame.transform.smoothscale(img, (max(1, round(img.get_width() * h / img.get_height())), h))
    sh = _shadow(img.get_width() * 0.9)
    surface.blit(sh, sh.get_rect(center=(x, ground_y + 2)))
    surface.blit(img, img.get_rect(midbottom=(x, ground_y + 4 - bob)))
    return True
