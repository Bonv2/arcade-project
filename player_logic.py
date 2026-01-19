import arcade

from math import sin, cos, atan2, degrees
from typing import Tuple

from constants import *


class Player(arcade.Sprite):
    def __init__(self, view: arcade.View):
        super().__init__()
        self.view = view

        self.idle_textures = [arcade.load_texture(f"./assets/player/idle/idle_{i}.png")
                              for i in range(2)]
        self.walk_textures = [arcade.load_texture(f"./assets/player/walk/walk_{i}.png")
                              for i in range(6)]

        self.animation_states = {"idle": self.idle_textures, "walk": self.walk_textures}

        self.texture = self.idle_textures[0]
        self.scale = PLAYER_SCALE
        self.speed = PLAYER_SPEED
        self.animation_frame = 0
        self.animation_timer = 0

        self.old_height = self.height

        self.animation_state = "idle"
        self.direction = Direction.RIGHT

        self.coyote_time = 0 # time since last on ground

    def determine_movement(self, mouse_coords: Tuple[float, float]) -> Tuple[float, float]:
        dx, dy = 0, 0
        m_x, m_y = mouse_coords # mouse
        p_x, p_y = self.position # player

        x = m_x - p_x
        y = m_y - p_y

        if abs(x) >= 35:
            if x < 0:
                dx -= self.speed
            elif x > 0:
                dx += self.speed
        if y >= 90:
            if self.coyote_time <= COYOTE_TIME:
                self.coyote_time = 999
                impulse = (0, PLAYER_JUMP_IMPULSE)
                self.view.physics_engine.apply_impulse(self, impulse)

        return (dx, dy)

    def update(self, mouse_coords: Tuple[float, float], delta_time: float = 1/60) -> None:
        is_on_ground = self.view.physics_engine.is_on_ground(self)
        if is_on_ground:
            self.coyote_time = 0
        else:
            self.coyote_time += delta_time

        dx, dy = self.determine_movement(mouse_coords)

        if dx != 0:
            self.animation_state = "walk"
            self.view.physics_engine.set_friction(self, 0)
        else:
            self.animation_state = "idle"
            self.view.physics_engine.set_friction(self, 1.0)
        if dx < 0:
            self.direction = Direction.LEFT
        elif dx > 0:
            self.direction = Direction.RIGHT

        self.view.physics_engine.apply_force(self, (dx, dy))

    def update_animation(self, delta_time: float = 1/60) -> None:
        self.animation_timer += delta_time
        if self.animation_timer >= 1 / ANIMATION_FPS:
            self.animation_timer = 0
            anim_lenght = len(self.animation_states[self.animation_state])
            self.animation_frame += 1
            if self.animation_frame >= anim_lenght:
                self.animation_frame = 0
            if self.direction == Direction.RIGHT:
                self.texture = self.animation_states[self.animation_state][self.animation_frame]
            else:
                self.texture = self.animation_states[self.animation_state][self.animation_frame].flip_horizontally()