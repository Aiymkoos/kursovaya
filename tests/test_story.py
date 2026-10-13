import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from kolenke.core.assets import ROOT
from kolenke.story.flags import Flags
from kolenke.story.graph import DialogueGraph, DialogueRunner, GraphError
from kolenke.story.journal import Journal

NIGHT1 = ROOT / "kolenke" / "data" / "night1.json"


def tiny(**over):
    data = {
        "start": "a",
        "speakers": {"x": "X"},
        "memories": {"m": {"who": "x", "text": "t"}},
        "nodes": {
            "a": {"speaker": "x", "text": "1", "choices": [
                {"text": "up", "next": "b", "set": {"f": True}, "memory": "m"},
                {"text": "hidden", "next": "b", "requires": {"f": True}},
            ]},
            "b": {"speaker": "x", "text": "2", "next": "c"},
            "c": {"end": True},
        },
    }
    data.update(over)
    return data


def runner(data):
    g = DialogueGraph(data)
    f, j = Flags(), Journal(g.memories)
    return DialogueRunner(g, f, j), f, j


def test_flags_check_and_roundtrip():
    f = Flags({"a": True})
    assert f.check({"a": True}) and not f.check({"a": False, "b": True})
    assert f.check(None)
    assert Flags.from_dict(f.to_dict()).get("a") is True


def test_journal_unique_and_unknown():
    j = Journal({"m": {"who": "x", "text": "t"}})
    assert j.add("m") and not j.add("m") and len(j) == 1
    with pytest.raises(KeyError):
        j.add("zzz")
    assert Journal.from_list(j.catalog, j.to_list()).has("m")


def test_runner_flow_sets_flags_and_memory():
    r, f, j = runner(tiny())
    assert r.has_choices and len(r.choices()) == 1  # «hidden» жасырын
    assert r.choose(0)
    assert f.get("f") and j.has("m") and r.node_id == "b"
    assert not r.choose(0)  # таңдауы жоқ түйін
    assert r.advance() and r.finished and not r.advance()


def test_hidden_choice_appears_after_flag():
    r, f, _ = runner(tiny())
    f.set("f")
    assert len(r.choices()) == 2


@pytest.mark.parametrize("bad", [
    {"start": "nope"},
    {"nodes": {"a": {"next": "zz"}}},
    {"nodes": {"a": {"next": "b", "end": True}, "b": {"end": True}}},
    {"nodes": {"a": {"memory": "q", "next": "b"}, "b": {"end": True}}},
    {"nodes": {"a": {"next": "b"}, "b": {"end": True}, "orphan": {"end": True}}},
    {"nodes": {"a": {"speaker": "ghost", "next": "b"}, "b": {"end": True}}},
])
def test_validation_rejects_bad_graphs(bad):
    with pytest.raises(GraphError):
        DialogueGraph(tiny(**bad))


def play(picks):
    """picks — таңдау нөмірлерінің тізбегі; соңына дейін жүреді."""
    g = DialogueGraph.load(NIGHT1)
    f, j = Flags(), Journal(g.memories)
    r = DialogueRunner(g, f, j)
    picks = iter(picks)
    for _ in range(100):
        if r.finished:
            return f, j
        if r.has_choices:
            assert r.choose(next(picks))
        else:
            r.advance()
    pytest.fail("диалог аяқталмады")


def test_night1_loads():
    g = DialogueGraph.load(NIGHT1)
    assert g.reachable() == set(g.nodes)


def test_night1_overhead_path_reveals_tell():
    f, j = play([0, 0, 0])  # жұмыс -> көрсет -> кез келген соңғы таңдау
    assert f.get("knows_overhead") and j.has("m_overhead") and j.has("m_bakery")
    assert not f.get("knows_tap")


def test_night1_hands_path_reveals_tap():
    f, j = play([1, 0])
    assert f.get("knows_tap") and j.has("m_tap")
    assert not f.get("knows_overhead")


def test_night1_sleep_path_learns_nothing():
    f, j = play([2, 1])
    assert len(j) == 0 and not f.get("knows_overhead")
    assert f.get("darkhan_called_name") is False


def test_dialogue_scene_runs_and_pops():
    import pygame
    from kolenke.core.game import Game
    from kolenke.scenes.dialogue import DialogueScene, JournalScene
    g = Game(fullscreen=False)
    try:
        g.push(DialogueScene(g, NIGHT1))
        sc = g.scene
        sc.update(10)  # мәтін толық шығады
        sc.handle_action("next")
        assert sc.runner.node_id == "n2"
        g.scene.handle_action("journal")
        assert isinstance(g.scene, JournalScene)
        g.step(1 / 60)
        g.scene.handle_action("journal")
        assert g.scene is sc
        g.step(1 / 60)
    finally:
        pygame.quit()
