import arcade
from constants import PLAYER_TEXTURE, PLAYER_SCALE

class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(PLAYER_TEXTURE)
        self.scale = PLAYER_SCALE