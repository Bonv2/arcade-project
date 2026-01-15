import arcade
from arcade import key
from pyglet.graphics import Batch

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
        self.player = Player()
        self.player.center_x = self.width / 2
        self.player.center_y = self.height / 2
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()

        self.player_list.draw()

    def on_update(self, delta_time):
        self.player.update(self.keys_pressed, delta_time)

    def on_key_press(self, symbol, modifiers):
        if symbol not in self.keys_pressed:
            self.keys_pressed.add(symbol)

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys_pressed:
            self.keys_pressed.remove(symbol)


def main():
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Alien game")
    arcade.set_background_color(arcade.color.SPACE_CADET)
    game.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()