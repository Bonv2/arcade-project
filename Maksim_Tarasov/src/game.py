# src/game.py
import arcade
import src.constants as c
from src.utils import create_sprite_or_solid, create_background_list, draw_text_with_outline, get_asset_path


class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, c.SCREEN_TITLE, update_rate=1 / 60)
        self.view_center_x = c.SCREEN_WIDTH / 2
        self.view_center_y = c.SCREEN_HEIGHT / 2

        self.jump_requested = False
        self.physics_engine = None

        self.bg_menu_list = create_background_list("background_menu.png")
        self.bg_game_list = create_background_list("background_game.png")

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.spike_list = arcade.SpriteList()
        self.menu_sprites = arcade.SpriteList()

        self.player_textures = ["player.png", "player1.png"]
        self.texture_index = 0

        self.menu_preview_sprite = create_sprite_or_solid(
            self.player_textures[self.texture_index],
            scale=c.SPRITE_SCALING_PLAYER,
            fallback_size=(40, 40)
        )
        self.menu_preview_sprite.position = (self.view_center_x, 120)
        self.menu_sprites.append(self.menu_preview_sprite)

        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()

        self.state = c.STATE_MENU
        self.level = 1
        self.level_results = {1: c.STATUS_NONE, 2: c.STATUS_NONE}

        self.ui_texts = {}
        self._init_ui_text()

    def _init_ui_text(self):
        self.ui_texts["title"] = arcade.Text("GEOMETRY DASH", self.view_center_x, 340,
                                             arcade.color.WHITE, 30, bold=True, anchor_x="center")
        self.ui_texts["lvl1"] = arcade.Text("1 - Легко", self.view_center_x - 100, 280,
                                            arcade.color.WHITE, 18, anchor_x="center")
        self.ui_texts["sep"] = arcade.Text("|", self.view_center_x, 280,
                                           arcade.color.WHITE, 18, anchor_x="center")
        self.ui_texts["lvl2"] = arcade.Text("2 - Средне", self.view_center_x + 100, 280,
                                            arcade.color.WHITE, 18, anchor_x="center")
        self.ui_texts["skin_hint"] = arcade.Text("C - Сменить модель", self.view_center_x, 240,
                                                 arcade.color.WHITE, 14, anchor_x="center")
        self.ui_texts["go_lvl_label"] = arcade.Text("", self.view_center_x, 300,
                                                    arcade.color.RED, 30, bold=True, anchor_x="center")
        self.ui_texts["go_status"] = arcade.Text("ПРОИГРЫШ", self.view_center_x, 250,
                                                 arcade.color.RED, 40, bold=True, anchor_x="center")
        self.ui_texts["go_retry"] = arcade.Text("R - Повторить | M - Меню", self.view_center_x, 150,
                                                arcade.color.WHITE, 20, anchor_x="center")

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.spike_list = arcade.SpriteList()
        self.jump_requested = False

        self.player_sprite = create_sprite_or_solid(
            self.player_textures[self.texture_index],
            scale=c.SPRITE_SCALING_PLAYER,
            fallback_size=(32, 32)
        )
        self.player_sprite.center_x = 100
        self.player_sprite.center_y = 150
        self.player_list.append(self.player_sprite)

        self.speed = c.PLAYER_SPEED_EASY if self.level == 1 else c.PLAYER_SPEED_MEDIUM
        self._generate_world()

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, platforms=self.wall_list, gravity_constant=c.GRAVITY
        )

    def _generate_world(self):
        for x in range(-200, 6000, 64):
            wall = create_sprite_or_solid("wall.png", scale=c.SPRITE_SCALING_WALL, fallback_size=(64, 64))
            wall.center_x, wall.center_y = x, 10
            self.wall_list.append(wall)

        spike_coords = (
            [600, 1100, 1500, 2000, 2500, 3000] if self.level == 1
            else [500, 800, 840, 1200, 1500, 1540, 1900, 2400, 2440, 2800, 3200]
        )
        self.end_of_level_x = 3500 if self.level == 1 else 3800

        for x in spike_coords:
            spike = create_sprite_or_solid("spike.png", scale=c.SPRITE_SCALING_SPIKE, fallback_size=(30, 40))
            spike.center_x, spike.center_y = x, 60
            self.spike_list.append(spike)

        finish = create_sprite_or_solid("finish.png", scale=1.0, fallback_size=(50, 600), color=arcade.color.GOLD)
        if getattr(finish, "texture", None):
            finish.scale = 600 / finish.height

        finish.center_x, finish.center_y = self.end_of_level_x, 300
        self.wall_list.append(finish)

    def _draw_background_list(self, lst, y_offset=0):
        if not lst:
            return
        for spr in lst:
            spr.center_x = self.view_center_x
            spr.center_y = self.view_center_y + y_offset
        lst.draw()

    def on_draw(self):
        self.clear()

        if self.state == c.STATE_MENU:
            self.gui_camera.use()
            self._draw_background_list(self.bg_menu_list, y_offset=-60)

            for lvl, key in ((1, "lvl1"), (2, "lvl2")):
                res = self.level_results[lvl]
                self.ui_texts[key].color = arcade.color.LIME_GREEN if res == c.STATUS_WIN else (
                    arcade.color.RED if res == c.STATUS_LOSS else arcade.color.WHITE
                )

            for k in ("title", "lvl1", "sep", "lvl2", "skin_hint"):
                draw_text_with_outline(self.ui_texts[k])
            self.menu_sprites.draw()

        elif self.state == c.STATE_GAME:
            self.gui_camera.use()
            self._draw_background_list(self.bg_game_list, y_offset=-60)
            self.camera.use()
            self.wall_list.draw()
            self.spike_list.draw()
            self.player_list.draw()

        else:  # GAME OVER
            self.gui_camera.use()
            self._draw_background_list(self.bg_game_list, y_offset=-60)
            self.ui_texts["go_lvl_label"].text = f"УРОВЕНЬ {self.level}"
            for k in ("go_lvl_label", "go_status", "go_retry"):
                draw_text_with_outline(self.ui_texts[k])

    def on_update(self, delta_time):
        if self.state != c.STATE_GAME:
            return

        self.player_sprite.change_x = self.speed
        if self.jump_requested and self.physics_engine.can_jump():
            self.player_sprite.change_y = c.JUMP_SPEED

        self.physics_engine.update()

        if not self.physics_engine.can_jump():
            self.player_sprite.angle -= 5
        else:
            self.player_sprite.angle = round(self.player_sprite.angle / 90) * 90

        if arcade.check_for_collision_with_list(self.player_sprite, self.spike_list):
            self.state = c.STATE_GAME_OVER
            if self.level_results[self.level] != c.STATUS_WIN:
                self.level_results[self.level] = c.STATUS_LOSS
            self.jump_requested = False

        if self.player_sprite.center_x >= self.end_of_level_x:
            self.state = c.STATE_MENU
            self.level_results[self.level] = c.STATUS_WIN
            self.jump_requested = False

        self.camera.position = (int(self.player_sprite.center_x + 150), int(self.view_center_y))

    def on_key_press(self, key, modifiers):
        if self.state == c.STATE_MENU:
            if key == arcade.key.KEY_1:
                self.level = 1
                self.setup()
                self.state = c.STATE_GAME
            elif key == arcade.key.KEY_2:
                self.level = 2
                self.setup()
                self.state = c.STATE_GAME
            elif key == arcade.key.C:
                self.texture_index = (self.texture_index + 1) % len(self.player_textures)
                new = create_sprite_or_solid(
                    self.player_textures[self.texture_index],
                    scale=c.SPRITE_SCALING_PLAYER,
                    fallback_size=(40, 40)
                )
                new.position = self.menu_preview_sprite.position
                self.menu_sprites.remove(self.menu_preview_sprite)
                self.menu_preview_sprite = new
                self.menu_sprites.append(self.menu_preview_sprite)

        elif self.state == c.STATE_GAME:
            if key in (arcade.key.SPACE, arcade.key.UP):
                self.jump_requested = True

        elif self.state == c.STATE_GAME_OVER:
            if key == arcade.key.R:
                self.setup()
                self.state = c.STATE_GAME
            elif key == arcade.key.M:
                self.state = c.STATE_MENU

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.SPACE, arcade.key.UP):
            self.jump_requested = False