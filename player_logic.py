import arcade

PLAYER_TEXTURE = "./assets/alien_placeholder.png"
PLAYER_SCALE = 0.5
PLAYER_SPEED = 300

class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(PLAYER_TEXTURE)
        self.scale = PLAYER_SCALE
        self.speed = PLAYER_SPEED

    def update(self, keys_pressed: set, delta_time: float = 1/60):
        dx = 0
        if arcade.key.LEFT in keys_pressed or arcade.key.A in keys_pressed:
            dx -= self.speed
        if arcade.key.RIGHT in keys_pressed or arcade.key.D in keys_pressed:
            dx += self.speed
        self.center_x += dx * delta_time