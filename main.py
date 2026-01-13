import arcade

from player_logic import Player

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600



class MainMenu(arcade.View):
    def on_show(self):
        pass

    def on_draw(self):
        self.clear()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            self.window.show_view(GameView())


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
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


def main():
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Alien game")
    arcade.set_background_color(arcade.color.OUTER_SPACE)
    game.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()