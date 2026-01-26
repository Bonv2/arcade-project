import arcade
import arcade.gui
import subprocess
import sys
import os


class MyWindow(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Меню выбора игр", resizable=True)

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.anchor_layout = arcade.gui.UIAnchorLayout()

        self.v_box = arcade.gui.UIBoxLayout(space_between=20)

        btn_maksim = arcade.gui.UIFlatButton(text="Максим Тарасов", width=250)
        btn_alien = arcade.gui.UIFlatButton(text="Alien-game (Владислав)", width=250)

        self.v_box.add(btn_maksim)
        self.v_box.add(btn_alien)

        @btn_maksim.event("on_click")
        def on_click_maksim(event):
            self.launch_script("Maksim_Tarasov/main.py")

        @btn_alien.event("on_click")
        def on_click_alien(event):
            self.launch_script("Alien-game/main.py")

        self.anchor_layout.add(
            child=self.v_box,
            anchor_x="center_x",
            anchor_y="center_y"
        )

        self.manager.add(self.anchor_layout)

    def launch_script(self, relative_path):
        base_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_path, relative_path)

        subprocess.Popen([sys.executable, script_path], cwd=os.path.dirname(script_path))


    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.manager.draw()


if __name__ == "__main__":
    window = MyWindow()
    arcade.run()