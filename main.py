"""«Көлеңке» ойынының кіру нүктесі."""
from kolenke.core.game import Game
from kolenke.scenes.menu import MenuScene


def main():
    game = Game(fullscreen=True)
    game.push(MenuScene(game))
    game.run()


if __name__ == "__main__":
    main()
