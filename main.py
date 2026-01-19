import math

import arcade
from pyglet.graphics import Batch
from typing import Tuple

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
        self.evil_text = arcade.Text(
            "Press SPACE... or else...", x=SCREEN_WIDTH / 2, y=SCREEN_HEIGHT / 2.2,
            anchor_x="center", anchor_y="center", batch=self.main_text_batch)

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
        self.player.center_x = self.width
        self.player.center_y = self.height / 2
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.all_sprites.append(self.player)

        tile_map = arcade.load_tilemap("assets/race.tmx")

        self.time = 0
        with open("assets/shaders/stars_shader.glsl", "r", encoding="utf-8") as file:
            self.stars_shader = arcade.experimental.Shadertoy((self.width, self.height), file.read())

        self.wall_list = tile_map.sprite_lists["walls"]
        self.background_list = tile_map.sprite_lists["background"]
        self.collision_list = tile_map.sprite_lists["walls"]

        self.all_sprites.extend(self.wall_list)

        self.world_camera = arcade.camera.Camera2D()
        self.mouse_pos = (0, 0)

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
            elasticity=0,
        )
        self.physics_engine.add_sprite_list(
            self.collision_list,
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            friction=WALL_FRICTION,
        )

    def on_show(self):
        pass

    def on_resize(self, width: int, height: int) -> bool | None:
        self.world_camera.update_values(arcade.rect.XYWH(self.width/2, self.height/2, self.width, self.height))
        self.stars_shader.resize((self.width, self.height))

    def on_draw(self):
        self.clear()

        self.stars_shader.render(time=self.time)

        self.world_camera.use()
        cam_pos = self.world_camera.position
        box_player = arcade.rect.XYWH(*self.player.position, 200, 150)
        self.background_list.draw()
        self.all_sprites.draw()
        mouse = self.world_to_cam(self.mouse_pos)
        arcade.draw_line(*self.player.position, *mouse, arcade.color.PUCE)
        arcade.draw_rect_outline(box_player, arcade.color.BLACK)
        arcade.draw_point(*cam_pos, arcade.color.RED, size=2)

    def update_world_camera(self):
        box_player = arcade.rect.XYWH(*self.player.position, 200, 150)

        old_x, old_y = self.world_camera.position
        cam_x, cam_y = self.world_camera.position
        cam_x = max(min(cam_x, box_player.right), box_player.left)
        cam_y = max(min(cam_y, box_player.top), box_player.bottom)
        if old_x != cam_x:
            cam_x = arcade.math.lerp(old_x, cam_x, 0.3)
        if old_y != cam_y:
            cam_y = arcade.math.lerp(old_y, cam_y, 0.3)
        self.world_camera.position = (cam_x, cam_y)

    def on_update(self, delta_time):
        self.physics_engine.step(1 / 120)
        self.physics_engine.step(1 / 120)
        self.time += delta_time

        self.update_world_camera()

        self.player.update(self.world_to_cam(self.mouse_pos), delta_time)
        self.player.update_animation(delta_time)

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif symbol == arcade.key.ESCAPE:
            self.window.set_fullscreen(False)
        elif symbol not in self.keys_pressed:
            self.keys_pressed.add(symbol)

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys_pressed:
            self.keys_pressed.remove(symbol)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.mouse_pos = (x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            player = self.player.position
            target = self.world_to_cam(self.mouse_pos)
            vector = target - player
            angle = math.atan2(vector.y, vector.x)
            x, y = math.cos(angle), math.sin(angle)

    def world_to_cam(self, xy: Tuple[float, float]) -> Tuple[float, float]:
        x, y = xy
        return (x + self.world_camera.position[0] - self.width / 2,
                y + self.world_camera.position[1] - self.height / 2)


def main():
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Alien game", resizable=True)
    game.set_minimum_size(1, 2)
    arcade.set_background_color(arcade.color.SPACE_CADET)
    game.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()