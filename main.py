"""«Көлеңке» ойынының кіру нүктесі.

python main.py            — толық экран
python main.py --windowed — терезеде
python main.py --selftest — бастапқы тексеру (терезесіз): ресурстар, сахналар, кадрлар
Браузерде (pygbag, WebAssembly) сол main.py asyncio арқылы іске қосылады.
"""
import argparse
import asyncio
import os
import sys
import traceback


def _selftest_body():
    from kolenke.core.game import Game
    from kolenke.scenes.fight import FightScene
    from kolenke.scenes.menu import MenuScene

    game = Game(fullscreen=False)
    game.push(MenuScene(game))
    for _ in range(30):
        game.step(1 / 60)
    game.scene.handle_action("confirm")       # «Жаңа ойын» -> ExploreScene
    for _ in range(30):
        game.step(1 / 60)
    game.push(FightScene(game, "darkhan"))
    for _ in range(60):
        game.step(1 / 60)
    return "SELFTEST OK: frames rendered, scenes=%d, audio=%s" % (len(game.scenes), game.audio.ok)


def selftest():
    """Нәтиже консольге, ал KOLENKE_SELFTEST_OUT берілсе — файлға жазылады
    (консольсіз .exe-де тексеру үшін)."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    out = os.environ.get("KOLENKE_SELFTEST_OUT")
    try:
        msg, code = _selftest_body(), 0
    except Exception:
        msg, code = "SELFTEST FAILED\n" + traceback.format_exc(), 1
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(msg)
    print(msg)
    return code


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


async def main_web():
    from kolenke.core.game import Game
    from kolenke.scenes.menu import MenuScene

    game = Game(fullscreen=False)
    game.push(MenuScene(game))
    await game.run_async()


if sys.platform == "emscripten":          # pygbag: main.py модуль ретінде орындалады
    asyncio.run(main_web())
elif __name__ == "__main__":
    sys.exit(main())
