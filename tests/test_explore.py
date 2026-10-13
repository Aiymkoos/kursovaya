import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from kolenke.core.assets import ROOT
from kolenke.core.game import Game
from kolenke.explore.locations import LocationError, load_locations
from kolenke.explore.player import Player
from kolenke.render.effects import Fade, ScreenShake
from kolenke.render.lighting import Lighting
from kolenke.scenes.dialogue import DialogueScene
from kolenke.scenes.explore import ExploreScene

LOCS = ROOT / "kolenke" / "data" / "locations.json"


@pytest.fixture
def game():
    g = Game(fullscreen=False)
    yield g
    pygame.quit()


def test_locations_valid_and_doors_link_back():
    locs = load_locations(LOCS)
    assert locs["corridor"].objects[0].to == "darkhan_room"
    assert any(o.to == "corridor" for o in locs["darkhan_room"].objects)


def test_location_validation(tmp_path):
    bad = tmp_path / "l.json"
    bad.write_text('{"a": {"width": 500, "name": "n", "start": 10, "objects": ['
                   '{"id": "d", "kind": "door", "x": 100, "w": 50, "label": "l",'
                   ' "to": "zzz", "spawn": 0}]}}', encoding="utf-8")
    with pytest.raises(LocationError):
        load_locations(bad)


def test_player_accelerates_and_clamps():
    p = Player(400)
    for _ in range(30):
        p.update(1 / 60, False, True, 2000)
    assert p.x > 400 and p.moving and p.facing == 1
    for _ in range(600):
        p.update(1 / 60, True, False, 2000)
    assert p.x == 50  # шектен шықпайды
    for _ in range(60):
        p.update(1 / 60, False, False, 2000)
    assert not p.moving  # тежеледі


def test_fade_runs_callback_once():
    f, hits = Fade((10, 10)), []
    f.start(lambda: hits.append(1), 0.1)
    for _ in range(60):
        f.update(1 / 60)
    assert hits == [1] and not f.active and f.alpha == 0


def test_shake_decays():
    s = ScreenShake()
    s.add(1.0)
    for _ in range(200):
        s.update(1 / 60)
    assert s.trauma == 0 and s.offset() == (0, 0)


def test_light_noise_range():
    vals = [Lighting.noise(t / 10, 5) for t in range(200)]
    assert min(vals) >= 0 and max(vals) <= 1


def test_door_transition_and_npc_dialogue(game):
    sc = ExploreScene(game)
    game.push(sc)
    sc.player.x = 1900
    assert sc.near.id == "door_darkhan"
    sc.handle_action("interact")
    for _ in range(60):
        game.step(1 / 60)
    assert sc.loc.id == "darkhan_room"
    sc.player.x = 900
    assert sc.near.id == "npc_darkhan"
    sc.handle_action("interact")
    assert isinstance(game.scene, DialogueScene)
    d = game.scene
    for _ in range(40):  # диалогты соңына дейін жүру (бірінші таңдау)
        d.update(10)
        if d.runner.finished:
            d.handle_action("next")
            break
        d.handle_action("choice1" if d.runner.has_choices else "next")
    assert game.scene is sc
    assert game.flags.get("night1_talk_done")
    assert sc.near is None or sc.near.kind != "npc"  # сөйлесу қайталанбайды


def test_held_movement(game):
    sc = ExploreScene(game)
    game.push(sc)
    x0 = sc.player.x
    game.held.add("right")
    for _ in range(30):
        game.step(1 / 60)
    assert sc.player.x > x0


def test_frame_time_budget(game):
    """60 FPS = 16.7 мс/кадр. Dummy-драйвермен өлшеу; шек жұмсақ (CI әртүрлі)."""
    sc = ExploreScene(game)
    game.push(sc)
    game.held.add("right")
    for _ in range(10):
        game.step(1 / 60)
    t0 = time.perf_counter()
    n = 120
    for _ in range(n):
        game.step(1 / 60)
    ms = (time.perf_counter() - t0) / n * 1000
    print(f"кадр уақыты: {ms:.2f} мс")
    assert ms < 33  # кемінде 30 FPS кез келген жағдайда
