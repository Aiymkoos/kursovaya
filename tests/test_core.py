import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from kolenke.core.assets import load_strings
from kolenke.core.game import Game
from kolenke.core.input import InputBuffer, action_for_key
from kolenke.scenes.menu import MenuScene, StubScene


@pytest.fixture
def game():
    g = Game(fullscreen=False)
    yield g
    pygame.quit()


def test_keymap_follows_spec():
    assert action_for_key(pygame.K_a) == "left"
    assert action_for_key(pygame.K_RIGHT) == "right"
    assert action_for_key(pygame.K_l) == "block"
    assert action_for_key(pygame.K_TAB) == "journal"
    assert action_for_key(pygame.K_F5) is None


def test_input_buffer_window():
    buf = InputBuffer(window=3)
    buf.push("light")
    for _ in range(2):
        buf.tick()
    assert buf.consume("light")
    assert not buf.consume("light")
    buf.push("heavy")
    for _ in range(4):
        buf.tick()
    assert not buf.consume("heavy")  # терезеден шықты


def test_kazakh_glyphs_in_font(game):
    font = game.assets.font(24)
    for ch in "ӘәҒғҚқҢңӨөҰұҮүҺһІі":
        assert font.metrics(ch)[0] is not None, ch
    assert "Көлеңке" == load_strings()["title"]


def test_menu_navigation_and_stub(game):
    game.push(MenuScene(game))
    game.scene.handle_action("confirm")  # «Жаңа ойын»
    assert isinstance(game.scene, StubScene)
    game.scene.handle_action("menu")
    assert isinstance(game.scene, MenuScene)
    game.step(1 / 60)  # кадр қатесіз сызылады


def test_menu_quit(game):
    game.push(MenuScene(game))
    game.scene.handle_action("down")
    game.scene.handle_action("confirm")  # «Шығу»
    assert game.running is False
