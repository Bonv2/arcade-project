import arcade
import random
from arcade.particles import (FadeParticle, Emitter, EmitBurst)
from typing import Tuple, List

from constants import *


def tp_mutator(p):
    p.change_y -= 0.03
    p.change_x *= 1.05
    p.change_y *= 1.05
    p.width *= 0.93
    p.height *= 0.93
    p.angle *= 0.99


def jump_mutator(p):
    p.change_y -= 0.03
    p.change_x *= 0.96
    p.change_y *= 0.8
    p.width *= 0.93
    p.height *= 0.93


def make_jump_particles(x, y):
    return Emitter(center_xy=(x, y),
        emit_controller=EmitBurst(12),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=JUMP_PARTICLE,
            change_xy=(random.uniform(-1, 1), random.uniform(0, 2)),
            center_xy=arcade.math.rand_on_line((-10, 0), (10, 0)),
            lifetime=random.uniform(1.0, 1.1),
            scale=random.uniform(0.3, 1.1),
            start_alpha=255, end_alpha=0,
            mutation_callback=jump_mutator,
        ),)


def make_tp_particles(x, y):
    return Emitter(center_xy=(x, y),
        emit_controller=EmitBurst(20),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=TP_PARTICLE,
            change_xy=arcade.math.rand_in_circle((0, 0), 2),
            center_xy=arcade.math.rand_in_circle((0, 0), 32),
            lifetime=random.uniform(1.0, 1.1),
            scale=random.uniform(0.3, 0.5),
            start_alpha=random.randint(200, 255), end_alpha=0,
            angle=random.uniform(-360, 360),
            mutation_callback=tp_mutator,
        ),)


class Player(arcade.Sprite):
    def __init__(self, view: arcade.View):
        super().__init__()
        self.view = view

        self.idle_textures = [arcade.load_texture(f"./assets/player/idle/idle_{i}.png")
                              for i in range(2)]
        self.walk_textures = [arcade.load_texture(f"./assets/player/walk/walk_{i}.png")
                              for i in range(6)]

        self.animation_states: dict[str, list[arcade.Texture]] = {"idle": self.idle_textures,
                                 "walk": self.walk_textures,
                                 "teleporting": self.idle_textures}

        self.texture = self.idle_textures[0]
        self.scale = PLAYER_SCALE
        self.speed = PLAYER_SPEED
        self.animation_frame = 0
        self.animation_timer = 0
        self.tp_timer = 0

        self.animation_state: str = "idle"
        self.direction: Direction = Direction.RIGHT
        self.emitters: List[Emitter] = []

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
                sound = arcade.Sound("assets/sounds/jump.wav")
                sound.play(loop=False, volume=0.5)
                self.coyote_time = 999
                impulse = (0, PLAYER_JUMP_IMPULSE)
                self.emitters.append(make_jump_particles(self.center_x, self.bottom + 3))
                self.view.physics_engine.apply_impulse(self, impulse)

        return (dx, dy)

    def update(self, mouse_coords: Tuple[float, float], keys_pressed: set, delta_time: float = 1/60) -> None:
        is_on_ground = self.view.physics_engine.is_on_ground(self)
        if is_on_ground:
            self.coyote_time = 0
        else:
            self.coyote_time += delta_time

        for emitter in self.emitters:
            emitter.update(delta_time)
            if emitter.can_reap():
                self.emitters.remove(emitter)

        if arcade.key.R in keys_pressed:
            self.view.physics_engine.set_friction(self, 1.0)
            self.tp_timer += delta_time
            self.animation_state = "teleporting"
            if self.tp_timer >= TIME_TILL_TP:
                self.tp_timer = 0
                self.animation_state = "idle"
                self.respawn_at_chkpnt()
            return
        else:
            self.tp_timer = 0
            self.animation_state = "idle"

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

    def respawn_at_chkpnt(self) -> None:
        checkpoint = self.view.get_cur_checkpoint()
        if checkpoint is None:
            return
        if checkpoint.reset_timer:
            self.view.cur_race_timer = 0
            self.view.timer_bleep = 0
        sound = arcade.Sound("assets/sounds/teleport.wav")
        sound.play(loop=False, volume=0.5)
        x, y = checkpoint.position
        y += 10
        self.emitters.append(make_tp_particles(*self.position))
        self.view.physics_engine.set_position(self, (x, y))
        self.view.physics_engine.set_velocity(self, (0, 0))

    def draw(self) -> None:
        if self.tp_timer > 0:
            angle = (self.tp_timer / TIME_TILL_TP) * 360
            arcade.draw_arc_outline(*self.position,
                                    width=80,
                                    height=80,
                                    color=arcade.color.WHITE,
                                    start_angle=0,
                                    end_angle=angle,
                                    border_width=7,)
        for emitter in self.emitters:
            emitter.draw()