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

        tile_map = arcade.load_tilemap("assets/alien_placeholder.tmx")

        self.wall_list = tile_map.sprite_lists["walls"]
        self.collision_list = tile_map.sprite_lists["collision"]

        self.all_sprites.extend(self.wall_list)

        self.camera = arcade.camera.Camera2D()


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
        self.physics_engine.add_sprite_list(
            self.collision_list,
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            friction=WALL_FRICTION,
        )

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()

        self.camera.use()
        cam_pos = self.camera.position
        box_player = arcade.rect.XYWH(*self.player.position, 200, 150)
        arcade.draw_rect_outline(box_player, arcade.color.BLACK)
        self.all_sprites.draw()

    def on_update(self, delta_time):
        self.physics_engine.step(1 / 120)
        self.physics_engine.step(1 / 120)

        box_player = arcade.rect.XYWH(*self.player.position, 200, 150)

        new_x, new_y = self.camera.position

        if new_x < box_player.left:
            new_x = box_player.left
        elif new_x > box_player.right:
            new_x = box_player.right
        if new_y > box_player.top:
            new_y = box_player.top
        elif new_y < box_player.bottom:
            new_y = box_player.bottom

        self.camera.position = (new_x, new_y)

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