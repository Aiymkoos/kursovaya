"""3-түн: басты кейіпкердің өзі айнала бастайды — экран қараяды, интерфейс жоғалады."""
import random

import pygame

_cache = {}


def hidden(level, threshold):
    """Интерфейс элементі осы дәрежеде жоғалады ма."""
    return level >= threshold


def protagonist_detail(level):
    """Басты кейіпкердің акценті мен бет белгілері тозуы: 1.0 -> 0.0."""
    return max(0.0, min(1.0, 1.0 - (level - 0.3) / 0.7))


def draw_corruption(surface, level, t):
    """Қараңғы перде + кездейсоқ «жоғалу» жолақтары."""
    if level <= 0.04:
        return
    size = surface.get_size()
    if size not in _cache:
        dark = pygame.Surface(size)
        dark.fill((0, 0, 0))
        _cache[size] = dark
    dark = _cache[size]
    dark.set_alpha(int(min(0.85, level) * 200))
    surface.blit(dark, (0, 0))
    rng = random.Random(int(t * 6))
    w, h = size
    for _ in range(int(level * 7)):
        y = rng.randrange(0, h)
        bar = pygame.Rect(0, y, w, rng.choice((2, 3, 5, 8)))
        surface.fill((0, 0, 0), bar)
