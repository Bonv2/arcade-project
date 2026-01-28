import arcade
import os
import math

from player_logic import Player
from arcade.future.light import Light, LightLayer
from arcade.gui import (UIManager, UITextureButton, UILabel, UISliderStyle,
                        UISlider, UISpace, UITextureToggle)
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from util import *
from constants import *


class MenuBackground(arcade.View):
    def __init__(self):
        super().__init__()
        self.window.set_fullscreen(read_settings().get("fullscreen", False))
        self.light_layer = None
        self.time = 0
        with open("assets/shaders/stars_shader.glsl", "r", encoding="utf-8") as file:
            self.stars_shader = arcade.experimental.Shadertoy((int(self.width), int(self.height)), file.read())
        self.setup()

    def setup(self):
        self.world_camera = arcade.Camera2D()
        self.light_layer = LightLayer(int(self.width), int(self.height))

        tile_map = arcade.load_tilemap("assets/levels/main_menu.tmx")
        self.wall_list = tile_map.sprite_lists["walls"]
        self.player = Player(self)
        special = tile_map.sprite_lists["special"]
        for sprite in special:
            if sprite.properties.get("type", None) == "player_spawn":
                self.player.bottom = sprite.bottom
                self.player.center_x = sprite.center_x

        radius = 500
        mode = 'soft'
        color = PLAYER_LIGHT
        self.player_light = Light(self.player.center_x, self.player.center_y, radius, color, mode)
        self.light_layer.add(self.player_light)

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        self.is_set_up = True

    def on_resize(self, width: int, height: int) -> bool | None:
        self.world_camera.match_window(viewport=True, projection=True)
        self.stars_shader.resize((width, height))
        self.light_layer.resize(int(self.width), int(self.height))

    def on_draw(self):
        self.clear()
        with self.light_layer:
            self.stars_shader.render(time=self.time)
            self.world_camera.use()
            self.wall_list.draw()
            self.player_list.draw()
        self.light_layer.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.F11:
            fullscreen = not self.window.fullscreen
            save_settings(fullscreen=fullscreen)
            self.window.set_fullscreen(not self.window.fullscreen)
        elif symbol == arcade.key.ESCAPE:
            self.window.close()

    def on_update(self, delta_time: float):
        if self.is_set_up:
            # self.time += delta_time
            self.world_camera.position = (self.player.position[0] + 100, self.player.position[1])
            self.player.update_animation(delta_time)


class MainMenu(MenuBackground):
    def __init__(self, game_view):
        self.manager: UIManager | None = None
        self.game_view = game_view
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)
        self.box1_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout, anchor_x="left")
        self.anchor_layout.add(self.box1_layout, anchor_x="right")
        self.manager.add(self.anchor_layout)

    def get_best_times_dict(self) -> Dict[str, Dict[int, float]]:
        try:
            contents = os.listdir("assets/saved/")
        except FileNotFoundError:
            os.mkdir("assets/saved")
            contents = os.listdir("assets/saved/")
        res = {}
        for file in contents:
            try:
                with open(f"assets/saved/{file}", "r") as file:
                    ok = [i.rstrip("\n").split(";") for i in file.readlines()]
                    ok = [(int(i[0]), float(i[1])) for i in ok]
                    ok = dict(ok)
            except FileNotFoundError:
                pass
            res[file.name[13:].rstrip(".txt")] = ok
        return res

    def setup_widgets(self):
        spacer = UISpace(width=220)
        self.box_layout.add(spacer)
        label = UILabel(text="Alien Game",
                        font_size=20,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="center")
        self.box_layout.add(label)
        texture_normal = arcade.load_texture("assets/ui/button_normal.png")
        texture_hovered = arcade.load_texture("assets/ui/button_hover.png")
        texture_pressed = arcade.load_texture("assets/ui/button_pressed.png")
        texture_button = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text="Play",
                                         scale=1.0)
        self.box_layout.add(texture_button)

        @texture_button.event("on_click")
        def on_click_texture_button(event):
            self.show_level_view()

        ok = self.get_best_times_dict()
        res = []
        for key in ok.keys():
            res.append(f"{key}:")
            for kkey in ok[key].keys():
                res.append(f"{str(kkey)}: {self.time_string(float(ok[key][kkey]))}")
        res = "\n".join(res)

        self.label1 = UILabel(text=res,
                        font_size=20,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="left",
                        multiline=True,)
        self.box1_layout.add(self.label1)

        texture_button2 = UITextureButton(texture=texture_normal,
                                          texture_hovered=texture_hovered,
                                          texture_pressed=texture_pressed,
                                          text="Options",
                                          scale=1.0)
        self.box_layout.add(texture_button2)

        spacer = UISpace(height=40)
        self.box_layout.add(spacer)

        texture_button1 = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text="Exit",
                                         scale=1.0)
        self.box_layout.add(texture_button1)

        @texture_button1.event("on_click")
        def on_click_texture_button(event):
            self.window.close()

        @texture_button2.event("on_click")
        def on_click_texture_button(event):
            self.manager.disable()
            options_view = OptionView(self)
            options_view.on_resize(int(self.width), int(self.height))
            self.window.show_view(options_view)

    def on_show_view(self):
        ok = self.get_best_times_dict()
        res = []
        for key in ok.keys():
            res.append(f"{key}:")
            for kkey in ok[key].keys():
                res.append(f"{str(kkey)}: {self.time_string(float(ok[key][kkey]))}")
        res = "\n".join(res)
        self.label1.text = res

    def on_draw(self):
        super().on_draw()
        if self.manager is not None:
            self.manager.draw()

    def show_level_view(self):
        level_view = LevelSelection(self)
        self.window.show_view(level_view)
        self.manager.disable()

    def time_string(self, time: float = 0) -> str:
        m = str(int(time // 60)).rjust(2, "0")
        s = str(math.floor(time % 60)).rjust(2, "0")
        ms = str(time - math.floor(time))[2:4].rjust(2, "0")
        return f"{m}:{s}:{ms}"


class LevelSelection(MenuBackground):
    def __init__(self, main_menu: MainMenu):
        self.manager = None
        super().__init__()
        self.main_menu = main_menu
        self.setup_ui()

    def setup_ui(self):
        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout, anchor_x="center")
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        label = UILabel(text="Level Selection",
                        font_size=20,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="center")
        self.box_layout.add(label)
        texture_normal = arcade.load_texture("assets/ui/button_normal.png")
        texture_hovered = arcade.load_texture("assets/ui/button_hover.png")
        texture_pressed = arcade.load_texture("assets/ui/button_pressed.png")
        levels = sorted([i.rstrip(".tmx") for i in os.listdir("assets/levels") if i.endswith(".tmx") and i != "main_menu.tmx"])
        if "tutorial" in levels:
            levels.remove("tutorial")
            levels.insert(0, "tutorial")
        for i, level in enumerate(levels):
            button = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text=f"{level}",
                                         scale=1.0)
            button.on_click = lambda event, val=level: self.show_game_view(val)
            self.box_layout.add(button)
        spacer = UISpace(height=30)
        self.box_layout.add(spacer)
        texture_button999 = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text="Back",
                                         scale=1.0)
        self.box_layout.add(texture_button999)

        @texture_button999.event("on_click")
        def on_click_texture_button(event):
            self.show_menu_view()

    def on_draw(self):
        super().on_draw()
        self.manager.draw()

    def show_game_view(self, level: str):
        self.main_menu.game_view.setup(level=level)
        self.main_menu.game_view.on_resize(self.width, self.height)
        self.window.show_view(self.main_menu.game_view)
        self.manager.disable()

    def show_menu_view(self):
        self.main_menu.manager.enable()
        self.main_menu.on_resize(int(self.width), int(self.height))
        self.main_menu.manager.on_resize(int(self.width), int(self.height))
        self.window.show_view(self.main_menu)
        self.manager.disable()


class PauseView(arcade.View):
    def __init__(self, view: arcade.View):
        super().__init__()
        self.parent = view
        self.rect = arcade.rect.XYWH(self.width / 2, self.height / 2,
                                     self.width, self.height)
        self.camera = arcade.Camera2D()
        self.setup()

    def on_resize(self, width, height):
        self.rect = arcade.rect.XYWH(self.width / 2, self.height / 2,
                                     self.width, self.height)
        self.camera.match_window(viewport=True, projection=True)
        self.manager.on_resize(int(self.width), int(self.height))

    def setup(self):
        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()  # Функция ниже

        self.anchor_layout.add(self.box_layout, anchor_x="center")  # Box в anchor
        self.manager.add(self.anchor_layout)  # Всё в manager

    def setup_widgets(self):
        label = UILabel(text="Pause",
                        font_size=20,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="center")
        self.box_layout.add(label)
        texture_normal = arcade.load_texture("assets/ui/button_normal.png")
        texture_hovered = arcade.load_texture("assets/ui/button_hover.png")
        texture_pressed = arcade.load_texture("assets/ui/button_pressed.png")
        texture_button1 = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text="Resume",
                                         scale=1.0)
        self.box_layout.add(texture_button1)

        texture_button = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text="Options",
                                         scale=1.0)
        self.box_layout.add(texture_button)
        spacer = UISpace(height=30,)
        self.box_layout.add(spacer)

        texture_button2 = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text="Back to menu",
                                         scale=1.0)
        self.box_layout.add(texture_button2)


        @texture_button1.event("on_click")
        def on_click_texture_button1(event):
            self.manager.disable()
            self.parent.on_resize(int(self.width), int(self.height))
            self.window.show_view(self.parent)

        @texture_button2.event("on_click")
        def on_click_texture_button2(event):
            self.manager.disable()
            self.parent.main_menu.manager.enable()
            self.parent.main_menu.on_resize(self.width, self.height)
            self.parent.main_menu.manager.on_resize(self.width, self.height)
            self.window.show_view(self.parent.main_menu)

        @texture_button.event("on_click")
        def on_click_texture_button(event):
            self.manager.disable()
            options_view = OptionView(self)
            options_view.on_resize(int(self.width), int(self.height))
            self.window.show_view(options_view)

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()
        self.camera.use()
        arcade.draw_rect_filled(self.rect, arcade.color.BLACK)
        self.manager.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.F11:
            fullscreen = not self.window.fullscreen
            save_settings(fullscreen=fullscreen)
            self.window.set_fullscreen(not self.window.fullscreen)
        elif symbol == arcade.key.ESCAPE:
            self.manager.disable()
            self.parent.on_resize(int(self.width), int(self.height))
            self.window.show_view(self.parent)


class OptionView(arcade.View):
    def __init__(self, view: arcade.View):
        super().__init__()
        self.parent = view
        self.rect = arcade.rect.XYWH(self.width / 2, self.height / 2,
                                self.width, self.height)
        self.setup()

    def setup(self):
        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout, anchor_x="center")
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        label = UILabel(text="Options",
                        font_size=20,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="center")
        self.box_layout.add(label)
        texture_normal = arcade.load_texture("assets/ui/button_normal.png")
        texture_hovered = arcade.load_texture("assets/ui/button_hover.png")
        texture_pressed = arcade.load_texture("assets/ui/button_pressed.png")
        volume_layout = UIBoxLayout(vertical=False, space_between=10)
        volume_label = UILabel(text=f"Volume: {read_settings().get("volume", 100)}%",
                               font_size=20,
                               text_color=arcade.color.WHITE,
                               width=300,
                               align="center"
                               )
        volume_layout.add(volume_label)
        ok = UISliderStyle()
        volume_slider = UISlider(minimum=0, maximum=100, step=1, # style={"normal":ok}
                                 value=read_settings().get("volume", 100))

        volume_layout.add(volume_slider)
        self.box_layout.add(volume_layout)

        fullscreen_layout = UIBoxLayout(vertical=False, space_between=10)

        fullscreen_label = UILabel(text="Fullscreen:",
                                   font_size=20,
                                   text_color=arcade.color.WHITE,
                                   width=300,
                                   align="center"
                                   )

        fullscreen_layout.add(fullscreen_label)
        toggle_on = arcade.load_texture("assets/ui/toggle_on.png")
        toggle_off = arcade.load_texture("assets/ui/toggle_off.png")
        self.fullscreen_toggle = UITextureToggle(on_texture=toggle_on,
                                            off_texture=toggle_off,
                                            width=32, height=32,)
        self.fullscreen_toggle.value = read_settings().get("fullscreen", self.window.fullscreen)

        fullscreen_layout.add(self.fullscreen_toggle)
        self.box_layout.add(fullscreen_layout)

        spacer = UISpace(height=30, )
        self.box_layout.add(spacer)


        texture_button = UITextureButton(texture=texture_normal,
                                         texture_hovered=texture_hovered,
                                         texture_pressed=texture_pressed,
                                         text="Back",
                                         scale=1.0)
        self.box_layout.add(texture_button)

        @volume_slider.event("on_change")
        def volume_slider_value(event):
            volume_label.text = f"Volume: {int(event.new_value)}%"
            save_settings(volume=int(event.new_value))

        @texture_button.event("on_click")
        def on_click_texture_button(event):
            self.manager.disable()
            self.parent.manager.enable()
            self.parent.on_resize(int(self.width), int(self.height))
            self.parent.manager.on_resize(int(self.width), int(self.height))
            self.window.show_view(self.parent)

        @self.fullscreen_toggle.event("on_click")
        def on_fullscreen_toggle(event):
            fullscreen = not self.window.fullscreen
            save_settings(fullscreen=fullscreen)
            self.window.set_fullscreen(fullscreen)

    def on_resize(self, width, height):
        self.manager.on_resize(self.width, self.height)

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()
        arcade.draw_rect_filled(self.rect, arcade.color.BLACK)
        self.manager.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.F11:
            fullscreen = not self.window.fullscreen
            save_settings(fullscreen=fullscreen)
            self.fullscreen_toggle.value = read_settings().get("fullscreen", self.window.fullscreen)
            self.window.set_fullscreen(not self.window.fullscreen)
        elif symbol == arcade.key.ESCAPE:
            self.manager.disable()
            self.parent.manager.enable()
            self.parent.manager.on_resize(int(self.width), int(self.height))
            self.window.show_view(self.parent)