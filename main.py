import arcade
import random
import math

import pymunk
from pyglet.graphics import Batch
from typing import Tuple

from constants import *
from extra_views import MainMenu, PauseView
from util import *
from player_logic import Player
from objects import Checkpoint, RaceEnd, Respawn, TimerDisplay, TextDisplay


class GameView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        self.keys_pressed = set()
        self.level: str | None = None
        self.time = 0
        self.freeze = True
        with open("assets/shaders/stars_shader.glsl", "r", encoding="utf-8") as file:
            self.stars_shader = arcade.experimental.Shadertoy((int(self.width), int(self.height)), file.read())
        self.world_camera = arcade.camera.Camera2D()
        self.ui_camera = arcade.camera.Camera2D()

    def setup(self, level: str) -> None:
        self.all_sprites = arcade.SpriteList()
        self.freeze = False

        self.level = level
        tile_map = arcade.load_tilemap(f"assets/levels/{self.level}.tmx")

        self.special_list = tile_map.sprite_lists["special"]
        self.level_end_list = arcade.SpriteList(use_spatial_hash=True)
        self.text_displays = arcade.SpriteList()

        self.player: Player | None = Player(self)
        for special in self.special_list:
            type = special.properties["type"]
            if type == "player_spawn":
                self.player.bottom = special.bottom
                self.player.center_x = special.center_x
            if type == "level_end":
                special.send_to = special.properties["send_to"]
                special.properties = None
                self.level_end_list.append(special)
            elif type == "text_display":
                text = special.properties["text"]
                color = (int(i )for i in special.properties["color"].split("."))
                draw_screen = special.properties["draw_screen"]
                font_size = special.properties["font_size"]
                pos = special.position
                size = (special.width, special.height)
                screen = TextDisplay(pos, size, text, color, font_size, draw_screen)
                self.text_displays.append(screen)


        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.all_sprites.append(self.player)


        self.wall_list = tile_map.sprite_lists["walls"]
        self.background_list = tile_map.sprite_lists["background"]
        self.collision_list = tile_map.sprite_lists["collisions"]
        self.laser_list = tile_map.sprite_lists["lasers"]
        self.checkpoint_list = arcade.SpriteList(use_spatial_hash=True)
        self.platform_list = tile_map.sprite_lists["platforms"]
        self.end_list = arcade.SpriteList(use_spatial_hash=True)
        self.display_list = arcade.SpriteList()

        self.cur_race: int | None = None
        self.cur_race_timer: float = 0

        self.cur_checkpoint: Checkpoint | None = None
        for platform in self.platform_list:
            left, right = platform.left, platform.right
            bottom, top = platform.bottom, platform.top
            platform.boundary_left = left + platform.boundary_left * 64
            platform.boundary_top = top + platform.boundary_top * 64
            platform.boundary_right = right + platform.boundary_right * 64
            platform.boundary_bottom = bottom + platform.boundary_bottom * 64

        displays = tile_map.sprite_lists["displays"]
        for display in displays:
            pos = display.position
            size = (display.width, display.height)
            race_id = display.properties["race_id"]
            self.display_list.append(TimerDisplay(pos, size, race_id, self.level))

        checkpoints = tile_map.sprite_lists["checkpoints"]
        for checkpoint in checkpoints:
            pos = checkpoint.position
            self.checkpoint_list.append(Checkpoint(pos))

        ends = tile_map.sprite_lists["ends"]
        for end in ends:
            pos = end.position
            race = end.properties["race_id"]
            rtype = end.properties["type"]
            self.end_list.append(RaceEnd(pos, rtype, race))

        self.all_sprites.extend(self.laser_list)
        self.all_sprites.extend(self.wall_list)

        self.mouse_pos = (0, 0)

        self.ui_list = arcade.SpriteList()

        self.windup = 0
        self.visual_timer = 0
        self.timer_bleep = 0
        self.mini_timer_bleep = 0
        self.timer_batch = Batch()
        arcade.load_font("assets/Seven Segment.ttf")
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
            collision_type="wall",
            friction=WALL_FRICTION,
        )
        self.physics_engine.add_sprite_list(
            self.platform_list,
            body_type=arcade.PymunkPhysicsEngine.KINEMATIC,
            collision_type="wall",
            friction=1.0,
        )

        for wall in self.collision_list:  # fix for weird collision
            width, height = wall.width / 2, wall.height / 2
            object = self.physics_engine.get_physics_object(wall)
            body = object.body
            old_shape = object.shape
            ffriction = old_shape.friction
            shape = pymunk.Poly(body, [(-width, -height), (-width, height),
                                       (width, height), (width, -height)])
            shape.friction = ffriction
            shape.collision_type = self.physics_engine.collision_types.index("wall")
            self.physics_engine.space.remove(old_shape)
            self.physics_engine.space.add(shape)

        for wall in self.platform_list:  # fix for weird collision
            width, height = wall.width / 2, wall.height / 2
            object = self.physics_engine.get_physics_object(wall)
            body = object.body
            old_shape = object.shape
            ffriction = old_shape.friction
            shape = pymunk.Poly(body, [(-width, -height), (-width, height),
                                       (width, height), (width, -height)])
            shape.friction = ffriction
            shape.collision_type = self.physics_engine.collision_types.index("wall")
            self.physics_engine.space.remove(old_shape)
            self.physics_engine.space.add(shape)

        self.physics_engine.add_sprite_list(
            self.laser_list,
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            collision_type="laser",
        )
        self.physics_engine.add_collision_handler(
            "player", "laser", pre_handler=self.respawn_player,
        )

    def respawn_player(self, *args):
        self.player.respawn_at_chkpnt()
        return False

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

    def on_resize(self, width: int, height: int) -> bool | None:
        self.world_camera.match_window(viewport=True, projection=True)
        self.ui_camera.match_window(viewport=True, projection=True)
        self.stars_shader.resize((int(self.width), int(self.height)))

    def on_draw(self) -> bool | None:
        self.clear()

        self.stars_shader.render(time=self.time)

        self.world_camera.use()
        if self.level is not None:
            self.background_list.draw()
            for display in self.display_list:
                display.draw()
            for display in self.text_displays:
                display.draw()
            self.checkpoint_list.draw()
            for checkpoint in self.checkpoint_list:
                checkpoint.draw()
            self.platform_list.draw()
            self.all_sprites.draw()
            self.player.draw()
            self.end_list.draw()
        else:
            arcade.draw_text("No level loaded!", self.width // 2, self.height // 2,)

        if DEBUG_INFO:
            cam_pos = self.world_camera.position
            self.collision_list.draw()
            arcade.draw_text(f"{self.cur_race_timer:0.2f} {self.cur_race}", x=cam_pos[0] - self.width / 2, y=cam_pos[1],
                             anchor_x="left", anchor_y="center")
            box_player = arcade.rect.XYWH(*self.player.position, 200, 150)
            mouse = self.world_to_cam(self.mouse_pos)
            arcade.draw_line(*self.player.position , *mouse, arcade.color.PUCE)
            arcade.draw_rect_outline(box_player, arcade.color.BLACK)
            arcade.draw_point(*cam_pos, arcade.color.RED, size=2)
        self.ui_camera.use()
        if self.level is not None:
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

    def update_non_phys_collisions(self): # all that uses collision but not physics, todo: maybe use pymunk sensors somehow (that should improve performance if i will need it)
        checkpoints_collisions = arcade.check_for_collision_with_list(self.player, self.checkpoint_list)
        checkpoint: Checkpoint
        for checkpoint in checkpoints_collisions:
            if not checkpoint.active:
                checkpoint.activate()
                self.cur_checkpoint = checkpoint
                for ccheckpoint in self.checkpoint_list:
                    if ccheckpoint != self.cur_checkpoint:
                        ccheckpoint.deactivate()

        ends_collisions = arcade.check_for_collision_with_list(self.player, self.end_list)
        node: RaceEnd
        for node in ends_collisions:
            type, race_id = node.get_action()
            if type == EndTypes.START and self.cur_race is None:
                self.cur_race = race_id
                self.cur_checkpoint = Respawn(node.position)
                sound = arcade.Sound("assets/sounds/race_start.wav")
                sound.play(loop=False, volume=0.5 * read_settings().get("volume", 100) / 100)
                for checkpoint in self.checkpoint_list:
                    checkpoint.deactivate()
                self.cur_race_timer = 0
            elif type == EndTypes.END and self.cur_race == race_id:
                self.flush_display_time(self.cur_race_timer, self.cur_race)
                self.unique_race_triggers(self.cur_race)
                self.cur_race = None

        level_end_collision = arcade.check_for_collision_with_list(self.player, self.level_end_list)
        if level_end_collision:
            level_end = level_end_collision[0]
            if level_end.send_to == "menu":
                self.main_menu.manager.enable()
                self.main_menu.on_resize(self.width, self.height)
                self.main_menu.manager.on_resize(self.width, self.height)
                self.window.show_view(self.main_menu)
                self.level = None
            else:
                self.setup(level_end.send_to)

    def unique_race_triggers(self, race_id: int):  # this is for handling triggers upon race completion (not used)
        pass

    def flush_display_time(self, cur_race_timer: float, cur_race: int):
        display: TimerDisplay
        for display in self.display_list:
            if display.race_id == cur_race:
                display.set_time(cur_race_timer)

    def update_platforms(self, delta_time: float = 1/60):
        for platform in self.platform_list:
            if platform.change_x > 0 and \
                    platform.right >= platform.boundary_right:
                platform.change_x *= -1
            elif platform.change_x < 0 and \
                    platform.left <= platform.boundary_left:
                platform.change_x *= -1
            if platform.change_y > 0 and \
                    platform.top >= platform.boundary_top:
                platform.change_y *= -1
            elif platform.change_y < 0 and \
                    platform.bottom <= platform.boundary_bottom:
                platform.change_y *= -1
            velocity = (platform.change_x * 1 / delta_time, platform.change_y * 1 / delta_time)
            self.physics_engine.set_velocity(platform, velocity)

    def on_update(self, delta_time: float = 1/60):
        if self.level is None or (self.freeze and self.level is not None):
            return
        self.physics_engine.step(1 / 120)
        self.update_platforms(1 / 120)
        self.physics_engine.step(1 / 120)
        self.update_platforms(1 / 120)
        self.time += delta_time

        self.update_world_camera()
        self.update_non_phys_collisions()

        self.display_list.update(delta_time)
        self.checkpoint_list.update(delta_time)
        self.end_list.update(delta_time)

        self.visual_timer += delta_time * self.windup
        if self.cur_race is not None:
            self.timer_bleep += delta_time
            self.mini_timer_bleep += delta_time
            self.cur_race_timer += delta_time
            self.windup += delta_time
            self.windup = min(1, self.windup)
        else:
            self.timer_bleep = 0
            self.mini_timer_bleep = 0
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
        if self.timer_bleep >= 1:
            self.timer_bleep -= 1
            sound = arcade.Sound("assets/sounds/timer_bleep.wav")
            sound.play(loop=False, volume=0.5 * read_settings().get("volume", 100) / 100)
        if self.mini_timer_bleep >= 0.05:
            self.mini_timer_bleep -= 0.05
            sound = arcade.Sound("assets/sounds/timer_bleep.wav")
            sound.play(loop=False, volume=0.1 * read_settings().get("volume", 100) / 100)

        self.player.update(self.world_to_cam(self.mouse_pos, self.world_camera), self.keys_pressed, delta_time)
        self.player.update_animation(delta_time)

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.F11:
            fullscreen = not self.window.fullscreen
            save_settings(fullscreen=fullscreen)
            self.window.set_fullscreen(fullscreen)
        elif symbol == arcade.key.ESCAPE:
            pause_view = PauseView(self)
            pause_view.on_resize(self.width, self.height)
            self.window.show_view(pause_view)
        elif symbol not in self.keys_pressed:
            self.keys_pressed.add(symbol)

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys_pressed:
            self.keys_pressed.remove(symbol)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.mouse_pos = (x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.keys_pressed.add(arcade.key.R)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            if arcade.key.R in self.keys_pressed:
                self.keys_pressed.remove(arcade.key.R)

    def world_to_cam(self, xy: Tuple[float, float], camera: arcade.Camera2D) -> Tuple[float, float]:
        x, y = xy
        return (x + camera.position[0] - self.width / 2,
                y + camera.position[1] - self.height / 2)

    def get_cur_checkpoint(self) -> Checkpoint | None:
        return self.cur_checkpoint # maybe store some checkpoints
        # and get the one furthest along path or smth
        # upd: why tho


if __name__ == "__main__":
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Alien game", resizable=True)
    game_view = GameView()
    main_menu = MainMenu(game_view)
    game_view.main_menu = main_menu
    game.set_minimum_size(1, 2)
    arcade.set_background_color(arcade.color.BLACK)
    game.show_view(main_menu)
    arcade.run()