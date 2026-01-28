import random
import arcade
import math
from typing import Tuple, Dict
from arcade.particles import (FadeParticle, Emitter, EmitInterval)
from pyglet.graphics import Batch
from constants import *
from util import read_settings


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


class Respawn(arcade.Sprite):
    def __init__(self, pos: Tuple[float, float]) -> None:
        super().__init__()
        self.position = pos
        self.reset_timer = True
        self.active: bool = False

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False


class Checkpoint(Respawn):
    def __init__(self, pos: Tuple[float, float]) -> None:
        super().__init__(pos)
        texture = arcade.load_spritesheet("assets/levels/tileset.png")
        rect = arcade.rect.LBWH(576, 320, 64, 64)
        texture = texture.get_texture(rect, y_up=True)
        self.texture = texture
        self.reset_timer = False
        self.emitter: Emitter | None = None

    def activate(self) -> None:
        super().activate()
        sound = arcade.load_sound("assets/sounds/activate_checkpoint.wav")
        sound.play(loop=False, volume=0.5 * read_settings().get("volume", 100) / 100)
        self.emitter = make_checkpoint_particles(*self.position)

    def deactivate(self) -> None:
        super().deactivate()
        self.emitter = None

    def draw(self) -> None:
        if self.active and self.emitter:
            self.emitter.draw()

    def update(self, delta_time: float = 1/60) -> None:
        if self.active and self.emitter:
            self.emitter.update(delta_time)


class RaceEnd(arcade.Sprite):
    def __init__(self, pos: Tuple[float, float], type: EndTypes = EndTypes.UNKNOWN, race: int = -1) -> None:
        super().__init__()
        self.position = pos
        self.time = (math.pi if (self.center_y // 64) % 2 == 1 else 0)
        texture = arcade.load_spritesheet("assets/levels/tileset.png")
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


class TimerDisplay(arcade.Sprite):
    def __init__(self, pos: Tuple[float, float], size: Tuple[float, float], race_id: int, level: str) -> None:
        super().__init__()
        self.level = level
        self.position = pos
        self.race_id = race_id
        self.width = size[0]
        self.height = size[1]
        self.visual_time = 0
        self.best_time = math.inf
        self.do_blinking = False
        self.batch = Batch()
        self.digits = []
        arcade.load_font("assets/Seven Segment.ttf")
        self.text_color = arcade.color.WHITE
        left_bottom = (self.center_x - self.width / 2, self.center_y - self.height / 2)
        self.info_text = arcade.Text(f"",
                                           x=left_bottom[0], y=left_bottom[1] + 60,
                                           anchor_x="left", anchor_y="bottom",
                                           color=self.text_color, font_size=25,
                                           font_name="Seven Segment", batch=self.batch)
        devs = DEVS_RECORDS.get(self.level, {}).get(self.race_id, None)
        devs = f"Dev record: {self.time_string(devs)}" if devs is not None else ""
        self.devs_best = arcade.Text(f"{devs}",
                                           x=left_bottom[0], y=left_bottom[1] + 120,
                                           anchor_x="left", anchor_y="bottom",
                                           color=arcade.color.RED, font_size=25,
                                           font_name="Seven Segment", batch=self.batch)
        self.setup()

    def setup(self) -> None:
        strin = self.time_string()
        step = self.width / len(strin)
        left_bottom = (self.center_x - self.width / 2, self.center_y - self.height / 2)
        for i, digit in enumerate(strin):
            self.digits.append(arcade.Text(f"{digit}",
                                           x=left_bottom[0] + step * i, y=left_bottom[1],
                                           anchor_x="left", anchor_y="bottom",
                                           color=self.text_color, font_size=40,
                                           font_name="Seven Segment", batch=self.batch))
        time = self.get_saved_race_time(self.race_id)
        self.load_best_time(time)

    def set_time(self, time: float) -> None:
        if time < self.best_time:
            self.best_time = time
            self.info_text.text = "new best!"
            self.save_best_time()
            self.do_blinking = True
        else:
            self.info_text.text = f"best: {self.time_string(self.best_time)}"
            self.do_blinking = False
        strin = self.time_string(time)
        for i, digit in enumerate(self.digits):
            digit.text = strin[i]

    def save_best_time(self) -> None: # the raceend object should be doing this todo: change this one day
        ok = self.get_best_times_dict()
        ok[self.race_id] = self.best_time
        ok = [f"{i};{ok[i]}\n" for i in ok.keys()]
        with open(f"assets/saved/{self.level}.txt", "w") as file:
            for line in ok:
                file.write(line)

    def get_best_times_dict(self) -> Dict[int, float]:
        try:
            with open(f"assets/saved/{self.level}.txt", "r") as file:
                ok = [i.rstrip("\n").split(";") for i in file.readlines()]
                ok = [(int(i[0]), float(i[1])) for i in ok]
                ok = dict(ok)
        except FileNotFoundError:
            return {}
        return ok

    def get_saved_race_time(self, race_id: int) -> float | None:
        ok = self.get_best_times_dict()
        return ok.get(race_id, None)

    def load_best_time(self, time: float | None) -> None:
        if time is None:
            return
        self.best_time = time
        self.info_text.text = f"best: {self.time_string(time)}"

    def time_string(self, time: float = 0) -> str:
        m = str(int(time // 60)).rjust(2, "0")
        s = str(math.floor(time % 60)).rjust(2, "0")
        ms = str(time - math.floor(time))[2:4].rjust(2, "0")
        return f"{m}:{s}:{ms}"

    def update_color(self, color) -> None:
        for digit in self.digits:
            digit.color = color

    def update(self, delta_time: float = 1/60) -> None:
        self.visual_time += delta_time
        if self.do_blinking:
            color = (255, 255, 255, int((math.sin(self.visual_time * 3) + 1) / 2 * 255))
            self.update_color(color)
        else:
            self.update_color(arcade.color.WHITE)

    def draw(self) -> None:
        rect = arcade.rect.XYWH(*self.position, self.width, self.height)
        arcade.draw_rect_filled(rect, arcade.color.BLACK)
        self.batch.draw()


class LevelEnd(arcade.Sprite):
    def __init__(self, pos: Tuple[float, float], size: Tuple[float, float], send_to: str) -> None:
        super().__init__()
        self.position = pos
        self.width, self.height = size
        self.send_to = send_to


class TextDisplay(arcade.Sprite):
    def __init__(self, pos: Tuple[float, float], size: Tuple[float, float], text: str, color: Tuple[int, int, int, int] = arcade.color.WHITE, font_size: int = 20, draw_screen: bool = True) -> None:
        super().__init__()
        self.position = pos
        self.width = size[0]
        self.height = size[1]
        self.batch = Batch()
        self.draw_screen = draw_screen
        self.info_text = arcade.Text(f"{text}",
                                           x=self.center_x, y=self.center_y,
                                           anchor_x="center", anchor_y="center",
                                           color=color, font_size=font_size,
                                           batch=self.batch, width=int(self.width), height=int(self.height),
                                     multiline=True)

    def draw(self) -> None:
        if self.draw_screen:
            rect = arcade.rect.XYWH(*self.position, self.width, self.height)
            arcade.draw_rect_filled(rect, arcade.color.BLACK)
        self.batch.draw()