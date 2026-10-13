"""Сквозной тест: ойын тек нақты пернелер оқиғаларымен өтеді (меню → 1-түн → 2-түн)."""
import pygame
import pytest

from kolenke.core.game import Game
from kolenke.core.save import has_save
from kolenke.scenes.dialogue import DialogueScene
from kolenke.scenes.explore import ExploreScene
from kolenke.scenes.fight import FightScene
from kolenke.scenes.menu import MenuScene
from kolenke.scenes.night_end import NightEndScene


@pytest.fixture
def game():
    g = Game(fullscreen=False)
    g.push(MenuScene(g))
    yield g
    pygame.quit()


def press(game, key, frames=2):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    game.step(1 / 60)
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))
    for _ in range(frames):
        game.step(1 / 60)


def hold(game, key, frames):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    for _ in range(frames):
        game.step(1 / 60)
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))
    for _ in range(25):                 # тежелу
        game.step(1 / 60)


def walk_until(game, key, predicate, limit=900):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    for _ in range(limit):
        game.step(1 / 60)
        if predicate():
            break
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))
    for _ in range(30):
        game.step(1 / 60)


def test_night1_with_real_keyboard_events(game):
    press(game, pygame.K_RETURN)                      # «Жаңа ойын»
    sc = game.scene
    assert isinstance(sc, ExploreScene) and sc.night == 1

    walk_until(game, pygame.K_d, lambda: sc.near is not None and sc.near.id == "door_darkhan")
    assert sc.near is not None and sc.near.id == "door_darkhan"
    press(game, pygame.K_e, frames=40)                # есік -> бөлме (қараңғыға өту)
    assert sc.loc.id == "darkhan_room"

    walk_until(game, pygame.K_d, lambda: sc.near is not None and sc.near.id == "npc_darkhan")
    press(game, pygame.K_e, frames=3)
    assert isinstance(game.scene, DialogueScene)

    d = game.scene
    for _ in range(60):                               # Space/1 арқылы диалогты аяқтау
        for _ in range(75):                           # мәтін теріліп біту үшін
            game.step(1 / 60)
        if d.runner.finished and d.text_done:
            press(game, pygame.K_SPACE)
            break
        press(game, pygame.K_1 if d.runner.has_choices else pygame.K_SPACE)
    assert game.scene is sc and game.flags.get("night1_talk_done")

    press(game, pygame.K_e, frames=3)                 # шайқас басталады
    fs = game.scene
    assert isinstance(fs, FightScene) and fs.enemy_name == "darkhan"
    fs.fight.enemy.hp = 6                             # шайқасты қысқарту (ақ жәшік)
    fs.fight.player.x, fs.fight.enemy.x = 560, 620
    hp0 = fs.fight.player.hp
    for _ in range(300):
        press(game, pygame.K_j, frames=14)
        if fs.fight.over:
            break
    assert fs.fight.over and fs.fight.outcome == "kill"
    for _ in range(150):
        game.step(1 / 60)
    assert fs.result == "win"
    press(game, pygame.K_SPACE)
    assert game.flags.get("darkhan_killed")
    assert isinstance(game.scene, NightEndScene)       # түн толық аяқталды -> қорытынды экран
    press(game, pygame.K_SPACE)
    assert game.night == 2 and has_save() and game.scene is sc and sc.night == 2
    assert sc.loc.id == "corridor"
