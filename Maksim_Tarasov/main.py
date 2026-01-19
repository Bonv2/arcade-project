# main.py
import arcade
from src.game import MyGame

if __name__ == "__main__":
    window = MyGame()
    window.setup()
    arcade.run()