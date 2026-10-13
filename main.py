"""«Көлеңке» ойынының кіру нүктесі.

python main.py            — толық экран
python main.py --windowed — терезеде
python main.py --selftest — бастапқы тексеру (терезесіз): ресурстар, сахналар, кадрлар
"""
import argparse
import os
import sys


def selftest():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    from kolenke.core.game import Game
    from kolenke.scenes.fight import FightScene
    from kolenke.scenes.menu import MenuScene

    game = Game(fullscreen=False)
    game.push(MenuScene(game))
    for _ in range(30):
        game.step(1 / 60)
    game.handle = None
    game.scene.handle_action("confirm")       # «Жаңа ойын» -> ExploreScene
    for _ in range(30):
        game.step(1 / 60)
    game.push(FightScene(game, "darkhan"))
    for _ in range(60):
        game.step(1 / 60)
    print("SELFTEST OK: frames rendered, scenes=%d, audio=%s" % (len(game.scenes), game.audio.ok))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Көлеңке")
    ap.add_argument("--windowed", action="store_true", help="терезеде іске қосу")
    ap.add_argument("--selftest", action="store_true", help="терезесіз тексеру")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    from kolenke.core.game import Game
    from kolenke.scenes.menu import MenuScene

    game = Game(fullscreen=not args.windowed)
    game.push(MenuScene(game))
    game.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
