import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from kolenke.combat.fight import Event
from kolenke.core.game import Game
from kolenke.scenes.fight import FightScene


class Idle:
    def decide(self, fight, me, opp):
        return 0, None, False


@pytest.fixture
def game():
    g = Game(fullscreen=False)
    yield g
    pygame.quit()


def make(game, ai=Idle):
    sc = FightScene(game, "darkhan", ai=lambda: ai())
    game.push(sc)
    return sc


def test_scene_runs_and_draws(game):
    sc = make(game)
    for _ in range(30):
        game.step(1 / 60)
    assert sc.fight.frame_no > 20


def test_parry_event_triggers_slowmo_and_shake(game):
    sc = make(game)
    sc._on_event(Event("parry", "darkhan", "player", 600, 500, 0, "overhead"))
    assert sc.slow_left > 0 and sc.shake.trauma > 0
    sc.update(1 / 60)
    assert sc.time_scale < 1.0
    for _ in range(120):
        sc.update(1 / 60)
    assert sc.time_scale == 1.0 or sc.time_scale > 0.9


def test_player_attacks_via_actions_and_wins(game):
    sc = make(game)
    sc.fight.enemy.hp = 8
    sc.fight.player.x, sc.fight.enemy.x = 500, 560
    sc.handle_action("light")
    for _ in range(240):
        game.step(1 / 60)
    assert sc.fight.over and sc.result == "win"
    sc.handle_action("next")
    assert game.flags.get("darkhan_fight_won")
    assert game.scene is not sc


def test_defeat_restarts_fight(game):
    sc = make(game)
    sc.fight.player.hp = 0
    sc.fight.player.state = "dead"
    sc.fight.tick()
    for _ in range(200):
        game.step(1 / 60)
    assert sc.result == "lose"
    sc.handle_action("next")
    assert sc.result is None and sc.fight.player.hp == 100


def test_fight_frame_budget(game):
    sc = make(game)
    sc._on_event(Event("hit", "darkhan", "player", 600, 500, 18, "overhead", True))
    for _ in range(10):
        game.step(1 / 60)
    t0 = time.perf_counter()
    for _ in range(120):
        game.step(1 / 60)
    ms = (time.perf_counter() - t0) / 120 * 1000
    print(f"бой кадры: {ms:.2f} мс")
    assert ms < 33


def test_restore_flow_sets_saved_flag_and_cuts_reserve(game):
    game.journal.catalog["m"] = {"who": "darkhan", "text": "t"}
    game.journal.add("m")
    sc = make(game)
    sc.fight.player.memory = 100
    sc.fight.enemy.hp = 10
    sc.handle_action("choice3")
    for _ in range(200):
        game.step(1 / 60)
    assert sc.fight.outcome == "restore" and sc.result == "win"
    sc.handle_action("next")
    assert game.flags.get("darkhan_saved") and game.reserve == 75


def test_kill_flow_sets_killed_flag_without_cost(game):
    sc = make(game)
    sc.fight.enemy.hp = 8
    sc.fight.player.x, sc.fight.enemy.x = 500, 560
    sc.handle_action("light")
    for _ in range(240):
        game.step(1 / 60)
    sc.handle_action("next")
    assert game.flags.get("darkhan_killed") and game.reserve == 100


def test_tell_marker_only_with_discovered_detail(game):
    sc = make(game)
    sc.fight.enemy.start_move("overhead")
    sc.fight.enemy.frame = 10
    surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
    sc._draw_tell(surf, (230, 150, 50))
    assert surf.get_bounding_rect().width == 0      # деталь белгісіз — белгі жоқ
    game.flags.set("knows_overhead")
    sc._draw_tell(surf, (230, 150, 50))
    assert surf.get_bounding_rect().width > 0
