import arcade


class MainMenu(arcade.View):
    def on_show(self):
        pass

    def on_draw(self):
        self.clear()


def main():
    game = arcade.Window()
    game.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()