"""Экрандағы интерфейс элементтері: түн индикаторы, журнал есептегіші."""
import pygame

GREY = (120, 120, 120)
ACCENT = (200, 60, 60)
WHITE = (230, 230, 230)


def draw_night_indicator(surface, font, label, night, total=3, pos=(40, 28)):
    """«1-түн» жазуы және ағымдағы түнді көрсететін үш шеңбер."""
    x, y = pos
    surface.blit(font.render(label, True, WHITE), (x, y))
    cx = x + font.size(label)[0] + 30
    for i in range(1, total + 1):
        center = (cx + (i - 1) * 26, y + font.get_height() // 2)
        if i < night:
            pygame.draw.circle(surface, GREY, center, 8)
        elif i == night:
            pygame.draw.circle(surface, ACCENT, center, 8)
        else:
            pygame.draw.circle(surface, GREY, center, 8, 2)


def draw_journal_counter(surface, font, count, right_edge):
    text = font.render(f"Tab · {count}", True, GREY)
    surface.blit(text, (right_edge - text.get_width(), 30))
