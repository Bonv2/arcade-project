import arcade
import random
import math
from pyglet.graphics import Batch
from typing import Tuple

from constants import *
from player_logic import Player
from objects import Checkpoint, RaceEnd


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
    def __init__(self) -> None:
        super().__init__()
        self.keys_pressed = set()

        self.all_sprites = arcade.SpriteList()

        self.player: Player | None = Player(self)
        self.player.center_x = 768
        self.player.center_y = 320
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.all_sprites.append(self.player)

        self.time = 0
        with open("assets/shaders/stars_shader.glsl", "r", encoding="utf-8") as file:
            self.stars_shader = arcade.experimental.Shadertoy((int(self.width), int(self.height)), file.read())

        tile_map = arcade.load_tilemap("assets/race.tmx")

        self.wall_list = tile_map.sprite_lists["walls"]
        self.background_list = tile_map.sprite_lists["background"]
        self.collision_list = tile_map.sprite_lists["walls"] # fixme: make some actual collisions, this will fix randomly getting stuck in ground
        self.checkpoints = arcade.SpriteList(use_spatial_hash=True)
        self.ends = arcade.SpriteList(use_spatial_hash=True)

        self.cur_race: int | None = None
        self.cur_race_timer: float = 0

        self.cur_checkpoint: Checkpoint | None = None

        checkpoints = tile_map.sprite_lists["checkpoints"]
        for checkpoint in checkpoints:
            pos = checkpoint.position
            self.checkpoints.append(Checkpoint(pos))

        ends = tile_map.sprite_lists["ends"]
        for end in ends:
            pos = end.position
            race = end.properties["race_number"]
            rtype = end.properties["type"]
            self.ends.append(RaceEnd(pos, rtype, race))

        self.all_sprites.extend(self.wall_list)

        self.world_camera = arcade.camera.Camera2D()
        self.ui_camera = arcade.camera.Camera2D()
        pos1 = self.ui_camera.position
        self.mouse_pos = (0, 0)

        self.ui_list = arcade.SpriteList()

        self.windup = 0
        self.visual_timer = 0
        self.timer_batch = Batch()
        self.timer_font = arcade.load_font("assets/Seven Segment.ttf")
        self.timer_text_bckgrnd0 = arcade.Text(f"0:00:00",
                                               x=100, y=60,
                                               anchor_x="center", anchor_y="center", batch=self.timer_batch,
                                               color=(0, 0, 0, 64), font_name="Seven Segment",
                                               font_size=42)
        self.timer_text = arcade.Text(f"0:00:00",
                                      x=100, y=60,
                                      anchor_x="center", anchor_y="center", batch=self.timer_batch,
                                      color=arcade.color.BLACK, font_name="Seven Segment",
                                      font_size=42)
        self.corner_textures = [arcade.load_texture(f"assets/timer_corner/timer_corner{i}.png") for i in range(6)]
        self.corner = arcade.Sprite("assets/timer_corner/timer_corner0.png")
        self.ui_list.append(self.corner)
        self.corner.scale = 0.7
        self.corner.left = 0
        self.corner.bottom = 0
        self.corner.visible = False
        self.timer_text_bckgrnd0.visible = False
        self.timer_text.visible = False
        self.corner_update()

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

    def corner_update(self):
        ok = min((self.visual_timer ** 0.5) * 0.5, 1)
        x, y = self.world_to_cam((100, 60), self.ui_camera)
        x1, y1 = self.world_to_cam((0, 0), self.ui_camera)
        self.timer_text_bckgrnd0.x = x + random.uniform(-10, 10) * ok
        self.timer_text_bckgrnd0.y = y + random.uniform(-10, 10) * ok
        self.timer_text.x = x
        self.timer_text.y = y
        self.corner.left = x1
        self.corner.bottom = y1
        m = int(self.cur_race_timer // 60)
        s = str(math.floor(self.cur_race_timer % 60)).rjust(2, "0")
        ms = str(self.cur_race_timer - math.floor(self.cur_race_timer))[2:4]
        self.timer_text_bckgrnd0.text = f"{m}:{s}:{ms}"
        self.timer_text.text = f"{m}:{s}:{ms}"
        frame = int(self.visual_timer * 15  * ok) % 6
        self.corner.texture = self.corner_textures[frame]

    def on_show(self):
        pass

    def on_resize(self, width: int, height: int) -> bool | None:
        self.world_camera.match_window(viewport=True, projection=True)
        self.ui_camera.match_window(viewport=True, projection=True)
        self.stars_shader.resize((int(self.width), int(self.height)))

    def on_draw(self) -> bool | None:
        self.clear()

        self.stars_shader.render(time=self.time)

        self.world_camera.use()
        self.background_list.draw()
        self.checkpoints.draw()
        for checkpoint in self.checkpoints:
            checkpoint.draw()
        self.all_sprites.draw()
        self.player.draw()
        self.ends.draw()

        if DEBUG_INFO:
            cam_pos = self.world_camera.position
            arcade.draw_text(f"{self.cur_race_timer:0.2f} {self.cur_race}", x=cam_pos[0] - self.width / 2, y=cam_pos[1],
                             anchor_x="left", anchor_y="center")
            box_player = arcade.rect.XYWH(*self.player.position, 200, 150)
            mouse = self.world_to_cam(self.mouse_pos)
            arcade.draw_line(*self.player.position, *mouse, arcade.color.PUCE)
            arcade.draw_rect_outline(box_player, arcade.color.BLACK)
            arcade.draw_point(*cam_pos, arcade.color.RED, size=2)

        self.ui_camera.use()
        self.ui_list.draw()
        self.timer_batch.draw()

    def update_world_camera(self):
        box_player = arcade.rect.XYWH(*self.player.position, 200, 150)

        old_x, old_y = self.world_camera.position
        cam_x, cam_y = self.world_camera.position
        cam_x = max(min(cam_x, box_player.right), box_player.left)
        cam_y = max(min(cam_y, box_player.top), box_player.bottom)
        if old_x != cam_x:
            cam_x = arcade.math.lerp(old_x, cam_x, 0.22)
        if old_y != cam_y:
            cam_y = arcade.math.lerp(old_y, cam_y, 0.22)
        self.world_camera.position = (cam_x, cam_y)

    def update_non_phys_collisions(self):
        checkpoints_collisions = arcade.check_for_collision_with_list(self.player, self.checkpoints)
        checkpoint: Checkpoint
        for checkpoint in checkpoints_collisions:
            if not checkpoint.active:
                checkpoint.activate()
                self.cur_checkpoint = checkpoint
                for ccheckpoint in self.checkpoints:
                    if ccheckpoint != self.cur_checkpoint:
                        ccheckpoint.deactivate()

        ends_collisions = arcade.check_for_collision_with_list(self.player, self.ends)
        node: RaceEnd
        for node in ends_collisions:
            type, race_id = node.get_action()
            if type == EndTypes.START and self.cur_race is None:
                self.cur_race = race_id
                self.cur_race_timer = 0
            elif type == EndTypes.END and self.cur_race == race_id:
                self.cur_race = None

    def on_update(self, delta_time):
        self.physics_engine.step(1 / 120)
        self.physics_engine.step(1 / 120)
        self.time += delta_time

        self.update_world_camera()
        self.update_non_phys_collisions()

        self.checkpoints.update(delta_time)
        self.ends.update(delta_time)

        self.visual_timer += delta_time * self.windup
        if self.cur_race is not None:
            self.cur_race_timer += delta_time
            self.windup += delta_time
            self.windup = min(1, self.windup)
        else:
            self.windup -= delta_time
            self.windup = max(0, self.windup)
        if self.windup != 0:
            self.corner.visible = True
            self.timer_text_bckgrnd0.visible = True
            self.timer_text.visible = True
            self.corner_update()
        else:
            self.corner.visible = False
            self.timer_text_bckgrnd0.visible = False
            self.timer_text.visible = False

        self.player.update(self.world_to_cam(self.mouse_pos, self.world_camera), self.keys_pressed, delta_time)
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
        pass

    def world_to_cam(self, xy: Tuple[float, float], camera: arcade.Camera2D) -> Tuple[float, float]:
        x, y = xy
        return (x + camera.position[0] - self.width / 2,
                y + camera.position[1] - self.height / 2)

    def get_cur_checkpoint(self) -> Checkpoint | None:
        return self.cur_checkpoint # maybe store some checkpoints
        # and get the one furthest along path or smth


def main():
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Alien game", resizable=True)
    game.set_minimum_size(1, 2)
    arcade.set_background_color(arcade.color.SPACE_CADET)
    game.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()