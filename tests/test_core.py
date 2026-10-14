import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from kolenke.core.assets import load_strings
from kolenke.core.game import Game
from kolenke.core.input import InputBuffer, action_for_key
from kolenke.scenes.explore import ExploreScene
from kolenke.scenes.dialogue import DialogueScene
from kolenke.scenes.menu import MenuScene


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


def test_menu_starts_prologue_then_exploration_and_returns(game):
    game.push(MenuScene(game))
    game.scene.handle_action("confirm")  # «Жаңа ойын» -> пролог
    assert isinstance(game.scene, DialogueScene) and game.scene.graph.id == "night0"
    game.step(1 / 60)  # пролог қатесіз сызылады
    game.scene.handle_action("menu")     # прологты өткізіп жіберу
    assert isinstance(game.scene, ExploreScene) and game.scene.night == 1
    game.scene.handle_action("menu")
    assert isinstance(game.scene, MenuScene)
    game.step(1 / 60)  # кадр қатесіз сызылады


def test_prologue_plays_to_the_end_and_unlocks_journal_entries(game):
    game.push(MenuScene(game))
    game.scene.handle_action("confirm")
    d = game.scene
    for _ in range(60):
        d.shown = len(d.text)                       # мәтін толық теріліп болды
        if d.runner.finished:
            d.handle_action("next")
            break
        d.handle_action("choice1" if d.runner.has_choices else "next")
    assert isinstance(game.scene, ExploreScene)
    assert game.flags.get("night0_talk_done") and game.flags.get("room13_key")
    assert {"m_room13", "m_first_shadow"} <= set(game.journal.to_list())


def test_menu_quit(game):
    game.push(MenuScene(game))
    game.scene.handle_action("down")
    game.scene.handle_action("confirm")  # «Шығу»
    assert game.running is False
