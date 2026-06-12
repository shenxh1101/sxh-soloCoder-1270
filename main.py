import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.game import Game


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
