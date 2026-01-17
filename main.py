import arcade
from pyglet.graphics import Batch

from constants import *
from player_logic import Player

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class MainMenu(arcade.View):
    def __init__(self):
        super().__init__()
        self.main_text_batch = Batch()
        self.game_title = arcade.Text(
            "Game about alien or smth", x=SCREEN_WIDTH / 2, y=SCREEN_HEIGHT / 2,
             anchor_x="center", anchor_y="center", batch = self.main_text_batch)

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()
        self.main_text_batch.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            self.window.show_view(GameView())


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.keys_pressed = set()

        self.all_sprites = arcade.SpriteList()

        self.player: Player | None = Player(self)
        self.player.center_x = self.width / 2
        self.player.center_y = self.height / 2
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.all_sprites.append(self.player)


        self.physics_engine = arcade.PymunkPhysicsEngine(damping=DEFAULT_DAMPING, gravity=GRAVITY_VECTOR)
        self.physics_engine.add_sprite(
            self.player,
            damping=PLAYER_DAMPING,
            friction=PLAYER_FRICTION,
            mass=PLAYER_MASS,
            moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
            collision_type="player",
            max_horizontal_velocity=PLAYER_MAX_HOR_SPEED,
            max_vertical_velocity=PLAYER_MAX_VERT_SPEED,
        )

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()

        self.all_sprites.draw()

    def on_update(self, delta_time):
        self.physics_engine.step(1 / 120)
        self.physics_engine.step(1 / 120)

        self.player.update(self.keys_pressed, delta_time)
        self.player.update_animation(delta_time)

    def on_key_press(self, symbol, modifiers):
        if symbol not in self.keys_pressed:
            self.keys_pressed.add(symbol)

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys_pressed:
            self.keys_pressed.remove(symbol)


def main():
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Alien game")
    arcade.set_background_color(arcade.color.SPACE_CADET)
    game.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()