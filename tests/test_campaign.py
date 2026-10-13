import json
import random

import pygame
import pytest

from kolenke.combat.fighter import load_combat_data
from kolenke.core.assets import ROOT
from kolenke.core.game import Game
from kolenke.core.save import delete_save, has_save, load_game, save_game, save_path
from kolenke.scenes.dialogue import DialogueScene
from kolenke.scenes.explore import ExploreScene
from kolenke.scenes.fight import FightScene
from kolenke.scenes.menu import MenuScene
from kolenke.scenes.night_end import (EndingScene, NightEndScene, ending_key,
                                      saved_count)
from kolenke.story.graph import DialogueGraph, DialogueRunner

DATA = ROOT / "kolenke" / "data"


@pytest.fixture
def game():
    g = Game(fullscreen=False)
    yield g
    pygame.quit()


# ---------- контент пен механиканың үйлесімділігі ----------
def all_graphs():
    return [DialogueGraph.load(DATA / f"night{n}.json") for n in (1, 2, 3)]


def set_flags(graph):
    out = set()
    for node in graph.nodes.values():
        out |= set(node.get("set", {}))
        for c in node.get("choices", []):
            out |= set(c.get("set", {}))
    return out


def test_every_tell_flag_can_be_learned_in_dialogue():
    data = load_combat_data()
    learnable = set().union(*(set_flags(g) for g in all_graphs()))
    for name in ("darkhan", "zhanel", "madina", "bekzat"):
        for move in data["fighters"][name]["moves"]:
            flag = data["moves"][move].get("tell_flag")
            assert flag in learnable, f"{name}/{move}: {flag} диалогта табылмайды"


def test_random_playthroughs_always_finish_and_choices_never_dead_end():
    for graph in all_graphs():
        for seed in range(40):
            rng = random.Random(seed)
            from kolenke.story.flags import Flags
            from kolenke.story.journal import Journal
            f, j = Flags({"darkhan_saved": seed % 2 == 0, "zhanel_saved": seed % 3 == 0}), Journal(graph.memories)
            r = DialogueRunner(graph, f, j)
            for _ in range(200):
                if r.finished:
                    break
                if r.has_choices:
                    assert r.choices(), f"{graph.id}/{r.node_id}: көрінетін таңдау жоқ"
                    assert r.choose(rng.randrange(len(r.choices())))
                else:
                    r.advance()
            assert r.finished, f"{graph.id}: seed {seed} аяқталмады"


def test_night2_order_flags_point_to_real_fighters():
    g = DialogueGraph.load(DATA / "night2.json")
    data = load_combat_data()
    for pick in (0, 1):
        from kolenke.story.flags import Flags
        from kolenke.story.journal import Journal
        f = Flags()
        r = DialogueRunner(g, f, Journal(g.memories))
        while r.node_id != "n3":
            r.advance()
        r.choose(pick)
        o1, o2 = f.get("order_1"), f.get("order_2")
        assert {o1, o2} == {"zhanel", "madina"} and f.get("night2_focus") == o2
        assert o1 in data["fighters"] and o2 in data["fighters"]


def test_all_who_names_have_strings():
    from kolenke.core.assets import load_strings
    s = load_strings()
    for g in all_graphs():
        for mem in g.memories.values():
            assert "who_" + mem["who"] in s


# ---------- сақтау ----------
def test_save_roundtrip(game):
    game.flags.set("darkhan_saved")
    game.journal.add("m_bakery")
    game.reserve = 75
    game.start_night(2)
    save_game(game)
    assert has_save()
    game.new_game_state()
    assert game.reserve == 100 and not game.flags.get("darkhan_saved")
    assert load_game(game)
    assert game.night == 2 and game.reserve == 75 and game.flags.get("darkhan_saved")
    assert game.journal.has("m_bakery")
    delete_save()
    assert not has_save()


@pytest.mark.parametrize("content", ["not json", "{}", '{"version": 99}',
                                     '{"version":1,"night":7,"flags":{},"journal":[],"reserve":1,"corruption":0}'])
def test_corrupted_save_is_rejected_without_changing_state(game, content):
    path = save_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    game.reserve = 55
    assert load_game(game) is False and game.reserve == 55


def test_save_ignores_unknown_journal_ids(game):
    path = save_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": 1, "night": 1, "flags": {}, "journal": ["m_bakery", "zzz"],
                                "reserve": 100, "corruption": 0.0}), encoding="utf-8")
    assert load_game(game) and game.journal.to_list() == ["m_bakery"]


def test_menu_shows_continue_only_with_save(game):
    game.push(MenuScene(game))
    assert len(game.scene.items) == 2
    save_game(game)
    game.scene.on_resume()
    assert len(game.scene.items) == 3
    game.scene.handle_action("confirm")        # «Жалғастыру»
    assert isinstance(game.scene, ExploreScene)


# ---------- түндер ағыны ----------
def test_ending_mapping_has_four_distinct_titles():
    assert [ending_key(i) for i in range(5)] == ["0", "1", "2", "3", "4"]
    data = json.load(open(DATA / "endings.json", encoding="utf-8"))
    assert len({data[k]["title"] for k in data}) == 4
    from kolenke.story.flags import Flags
    assert saved_count(Flags({"darkhan_saved": True, "bekzat_saved": True, "zhanel_killed": True})) == 2


def test_night2_flow_two_fights_in_order(game):
    game.start_night(2)
    sc = ExploreScene(game)
    game.push(sc)
    sc._go(sc.locs["corridor"].objects[0])      # есік арқылы емес — тікелей бөлмеге
    sc.loc = sc.locs["girls_room"]
    sc.player.x = 780
    obj = sc.near
    assert obj.id in ("npc_zhanel", "npc_madina")
    sc.handle_action("interact")
    d = game.scene
    assert isinstance(d, DialogueScene)
    while not d.runner.finished:                # Жанельмен сөйлесіп, бірінші таңдауды қайталау
        d.update(10)
        d.handle_action("choice1" if d.runner.has_choices else "next")
    d.update(10)
    d.handle_action("next")
    assert game.flags.get("order_1") == "madina" and game.flags.get("night2_talk_done")
    sc.handle_action("interact")
    assert isinstance(game.scene, FightScene) and game.scene.enemy_name == "madina"
    game.flags.set("madina_fight_won")
    game.pop()
    sc.handle_action("interact")
    assert game.scene.enemy_name == "zhanel"
    # Жанельде дайындық белгілері бар (сөйлескен), Мадинада жоқ
    assert game.flags.get("knows_crash") or game.flags.get("knows_snare")
    assert not game.flags.get("knows_stitch")


def test_night_complete_opens_summary_then_next_night(game):
    sc = ExploreScene(game)
    game.push(sc)
    game.flags.set("night1_talk_done")
    game.flags.set("darkhan_fight_won")
    game.flags.set("darkhan_saved")
    sc.update(1 / 60)
    assert isinstance(game.scene, NightEndScene)
    game.scene.handle_action("next")
    assert game.night == 2 and has_save()
    assert game.scene is sc and sc.night == 2 and sc.loc.id == "corridor"


def test_final_night_leads_to_ending_and_back_to_menu(game):
    game.push(MenuScene(game))
    game.start_night(3)
    sc = ExploreScene(game)
    game.push(sc)
    for f in ("night3_talk_done", "bekzat_fight_won", "darkhan_saved", "zhanel_saved", "madina_saved"):
        game.flags.set(f)
    sc.update(1 / 60)
    assert isinstance(game.scene, NightEndScene)
    game.scene.handle_action("next")
    end = game.scene
    assert isinstance(end, EndingScene) and end.count == 3
    for _ in range(40):
        end.update(10)
        end.handle_action("next")
        if not isinstance(game.scene, EndingScene):
            break
        game.step(1 / 60)
    assert isinstance(game.scene, MenuScene) and not has_save()


def test_corruption_grows_only_on_night3_and_hides_ui(game):
    game.tick_corruption(100)
    assert game.corruption == 0
    game.start_night(3)
    assert game.corruption == 0.25
    game.tick_corruption(200)
    assert game.corruption == 0.92
    sc = ExploreScene(game)
    game.push(sc)
    game.step(1 / 60)   # интерфейс жасырылғанда да қатесіз сызылады
    sc2 = FightScene(game, "bekzat", night=3)
    game.push(sc2)
    game.step(1 / 60)
