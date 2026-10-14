"""Ресурстарды (шрифт, мәтін) жүктеу және кэштеу."""
import json
import sys
from pathlib import Path

import pygame

# PyInstaller (.exe) ішінде ресурстар sys._MEIPASS-та жатады
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
FONT_REGULAR = ROOT / "assets" / "fonts" / "DejaVuSans.ttf"
FONT_BOLD = ROOT / "assets" / "fonts" / "DejaVuSans-Bold.ttf"
STRINGS_PATH = ROOT / "kolenke" / "data" / "strings_kk.json"


def load_strings(path=STRINGS_PATH):
    """Интерфейс мәтіндерін JSON-нан оқиды (кодта қатар жоқ)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Assets:
    """Шрифттер кэші: бір өлшем — бір Font объектісі."""

    def __init__(self):
        self._fonts = {}

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            path = FONT_BOLD if bold else FONT_REGULAR
            self._fonts[key] = pygame.font.Font(str(path), size)
        return self._fonts[key]


_images = {}
BG_FILES = {"darkhan_room": "room_darkhan", "girls_room": "room_girls", "bekzat_room": "room_bekzat",
            "corridor": "corridor", "hall_entrance": "hall_entrance"}


def load_image(rel, size=None, cover=True):
    """assets/<rel>.png суретін жүктейді (кэштеледі). Файл жоқ болса — None (код сызған алмастыру қолданылады).

    size берілсе: cover — кадрды толтырады (артығын қияды), әйтпесе — сыйғызады."""
    key = (rel, size, cover)
    if key not in _images:
        path = ROOT / "assets" / (rel + ".png")
        img = None
        if path.exists():
            try:
                img = pygame.image.load(str(path))
                img = img.convert_alpha() if pygame.display.get_surface() else img
            except pygame.error:
                img = None
        if img is not None and size:
            iw, ih = img.get_size()
            k = max(size[0] / iw, size[1] / ih) if cover else min(size[0] / iw, size[1] / ih)
            nw, nh = max(1, round(iw * k)), max(1, round(ih * k))
            img = pygame.transform.smoothscale(img, (nw, nh))
            if cover:
                img = img.subsurface(((nw - size[0]) // 2, (nh - size[1]) // 2, *size)).copy()
        _images[key] = img
    return _images[key]
