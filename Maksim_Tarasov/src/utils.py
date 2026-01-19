# src/utils.py
import os
import arcade
from src.constants import SCREEN_WIDTH, SCREEN_HEIGHT


def get_asset_path(filename):
    return os.path.join("assets", filename)


def create_sprite_or_solid(filename, scale=1.0, fallback_size=(32, 32), color=arcade.color.CYAN):
    path = get_asset_path(filename)
    if os.path.isfile(path):
        return arcade.Sprite(path, scale=scale)

    w, h = fallback_size
    return arcade.SpriteSolidColor(w, h, color)


def create_background_list(filename):
    path = get_asset_path(filename)
    spr = create_sprite_or_solid(filename, fallback_size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=arcade.color.BLACK)

    if getattr(spr, "texture", None):
        scale = max(SCREEN_WIDTH / spr.width, SCREEN_HEIGHT / spr.height)
        spr.scale = scale

    lst = arcade.SpriteList()
    lst.append(spr)
    return lst


def draw_text_with_outline(text_obj):
    ox, oy = text_obj.x, text_obj.y
    orig_color = text_obj.color
    text_obj.color = arcade.color.BLACK

    offsets = [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]
    for dx, dy in offsets:
        text_obj.x, text_obj.y = ox + dx, oy + dy
        text_obj.draw()

    text_obj.x, text_obj.y = ox, oy
    text_obj.color = orig_color
    text_obj.draw()