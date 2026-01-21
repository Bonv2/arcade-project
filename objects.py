import random
import arcade
import math
from typing import Tuple
from arcade.particles import (FadeParticle, Emitter, EmitBurst, EmitInterval, EmitMaintainCount)
from constants import *


def checkpoint_mutator(p) -> None:
    p.change_y += 0.03
    p.change_x *= 0.96
    p.change_y *= 0.98


def make_checkpoint_particles(x: float | int, y: float | int) -> Emitter:
    rect = arcade.rect.XYWH(0, -10, 64, 20)
    return Emitter(center_xy=(x, y),
        emit_controller=EmitInterval(0.02),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=CHECKPOINT_PARTICLE,
            change_xy=(random.uniform(-1, 1), random.uniform(0, 6)),
            center_xy=arcade.math.rand_in_rect(rect),
            lifetime=random.uniform(1.0, 1.5),
            scale=random.uniform(0.9, 1.1),
            start_alpha=225, end_alpha=0,
            mutation_callback=checkpoint_mutator,
        ),)


class Checkpoint(arcade.Sprite):
    def __init__(self, pos) -> None:
        super().__init__()
        self.position = pos
        texture = arcade.load_spritesheet("assets/tileset.png")
        rect = arcade.rect.LBWH(576, 320, 64, 64)
        texture = texture.get_texture(rect, y_up=True)
        self.texture = texture

        self.active: bool = False
        self.emitter: Emitter | None = None

    def activate(self) -> None:
        self.active = True
        self.emitter = make_checkpoint_particles(*self.position)

    def deactivate(self) -> None:
        self.active = False
        self.emitter = None

    def draw(self) -> None:
        if self.active and self.emitter:
            self.emitter.draw()

    def update(self, delta_time: float = 1/60) -> None:
        if self.active and self.emitter:
            self.emitter.update(delta_time)


class RaceEnd(arcade.Sprite):
    def __init__(self, pos, type: EndTypes = EndTypes.UNKNOWN, race: int = -1) -> None:
        super().__init__()
        self.position = pos
        self.time = (math.pi if (self.center_y // 64) % 2 == 1 else 0)
        texture = arcade.load_spritesheet("assets/tileset.png")
        rect = arcade.rect.LBWH(576, 384, 64, 64)
        texture = texture.get_texture(rect, y_up=True)
        self.texture = texture
        self.race = race
        if type == "start":
            self.type = EndTypes.START
        elif type == "end":
            self.type = EndTypes.END
        elif type == "intermediate":
            self.type = EndTypes.INTERMEDIATE
        else:
            self.type = EndTypes.UNKNOWN

    def get_action(self) -> Tuple[EndTypes, int]:
        return (self.type, self.race)

    def update(self, delta_time: float = 1/60) -> None:
        self.time += delta_time * 2
        self.color = (255, 255, 255, 128 + int(((math.sin(self.time) + 1) / 2) * 128))