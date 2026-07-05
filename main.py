from kivy.app import App
from gui import BBUI
from brain import process


class BBApp(App):
    def build(self):
        self.title = "BB V4"
        return BBUI(process)


if __name__ == "__main__":
    BBApp().run()
