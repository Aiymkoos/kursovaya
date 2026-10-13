"""Ресурстарды (шрифт, мәтін) жүктеу және кэштеу."""
import json
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[2]
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
