"""Есепке арналған скриншоттар: ойын сахналарын терезесіз сызып, PNG-ға сақтайды.

Іске қосу:  python tools/screenshots.py [шығыс_папка]
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("KOLENKE_SAVE_DIR", tempfile.mkdtemp())

import pygame

from kolenke.core.game import Game
from kolenke.scenes.dialogue import DialogueScene, JournalScene
from kolenke.scenes.explore import ExploreScene
from kolenke.scenes.fight import FightScene
from kolenke.scenes.menu import MenuScene
from kolenke.scenes.night_end import EndingScene, NightEndScene

DATA = ROOT / "kolenke" / "data"


class Script:
    def __init__(self, plan, hold_until=-1):
        self.plan, self.hold_until, self.n = plan, hold_until, 0

    def decide(self, fight, me, opp):
        self.n += 1
        return 0, self.plan.get(self.n), self.n <= self.hold_until


def fresh(game, night=1):
    game.scenes.clear()
    game.new_game_state()
    game.start_night(night)


def shot(game, out, name, frames=2):
    game.fade_in = 0
    for _ in range(frames):
        game.step(1 / 60)
    pygame.image.save(game.screen, str(out / name))
    print("saved", name)


def dialogue(game, fn, picks, night):
    s = DialogueScene(game, DATA / fn, night=night)
    game.push(s)
    for p in picks:
        s.update(10)
        s.handle_action("next" if p is None else f"choice{p}")
    s.update(10)
    return s


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "report" / "img"
    out.mkdir(parents=True, exist_ok=True)
    g = Game(fullscreen=False)

    fresh(g)
    g.push(MenuScene(g))
    shot(g, out, "01_menu.png", 20)

    fresh(g)
    sc = ExploreScene(g)
    g.push(sc)
    sc.player.x = 1800
    sc.cam = sc._target_cam()
    shot(g, out, "02_corridor.png", 40)

    sc._go(sc.locs["corridor"].objects[1])
    sc.player.x = 830
    sc.cam = sc._target_cam()
    shot(g, out, "03_room.png", 40)

    fresh(g)
    dialogue(g, "night1.json", [None, None, None], 1)
    shot(g, out, "04_dialogue_choices.png")
    fresh(g)
    dialogue(g, "night1.json", [None, None, None, 1, None, 1, None, None], 1)
    shot(g, out, "05_dialogue_fading.png")
    fresh(g)
    dialogue(g, "night1.json", [None, None, None, 1, None, 1, None, None, None, 1], 1)
    shot(g, out, "06_dialogue_shadow.png")

    fresh(g)
    dialogue(g, "night1.json", [None, None, None, 1, None, 1], 1)
    g.push(JournalScene(g))
    shot(g, out, "07_journal.png")

    fresh(g, 2)
    dialogue(g, "night2.json", [None, None], 2)
    shot(g, out, "08_night2_cast.png")

    # шайқас: дайындық белгісі
    fresh(g)
    g.flags.set("knows_overhead")
    fs = FightScene(g, "darkhan", ai=lambda: Script({1: "overhead"}))
    g.push(fs)
    fs.fight.player.x, fs.fight.enemy.x = 540, 700
    for _ in range(300):
        g.step(1 / 60)
        if fs.fight.enemy.state == "overhead" and fs.fight.enemy.frame >= 16:
            break
    shot(g, out, "09_fight_tell.png", 1)

    # парирлеу
    fresh(g)
    g.flags.set("knows_overhead")      # дайындық белгісі белгілі -> қимыл толық ұзақтықта
    fs = FightScene(g, "darkhan", ai=lambda: Script({1: "overhead"}))
    g.push(fs)
    fs.fight.controllers[fs.fight.player] = Script({31: "block"}, hold_until=40)
    fs.fight.player.x, fs.fight.enemy.x = 540, 640
    for _ in range(300):
        g.step(1 / 60)
        if any(p[0] == g.strings["fight_parry"] for p in fs.popups):
            break
    shot(g, out, "10_fight_parry.png", 1)

    # қайтару мүмкіндігі
    fresh(g)
    g.journal.add("m_bakery")
    fs = FightScene(g, "darkhan", ai=lambda: Script({}))
    g.push(fs)
    fs.fight.enemy.hp = 25
    fs.fight.player.memory = 70
    fs.fight.player.hp = 70
    shot(g, out, "11_fight_restore_hint.png", 5)

    fresh(g)
    for f in ("darkhan_saved", "zhanel_saved", "madina_killed"):
        g.flags.set(f)
    g.push(NightEndScene(g, 2))
    g.scene.update(0.5)
    shot(g, out, "12_night_end.png")

    fresh(g, 3)
    g.corruption = 0.6
    fs = FightScene(g, "bekzat", night=3, ai=lambda: Script({}))
    g.push(fs)
    shot(g, out, "13_night3_corruption.png", 30)

    fresh(g)
    for f in ("darkhan_saved", "zhanel_saved", "madina_saved", "bekzat_saved"):
        g.flags.set(f)
    g.push(EndingScene(g))
    g.scene.update(5)
    shot(g, out, "14_ending.png")
    pygame.quit()


if __name__ == "__main__":
    main()
