import traceback
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView


def _build_error_screen(message):
    scroll = ScrollView()
    label = Label(
        text=message,
        size_hint_y=None,
        halign="left",
        valign="top",
        color=(1, 0.35, 0.35, 1),
        padding=(16, 16)
    )
    label.bind(width=lambda w, val: setattr(label, "text_size", (val, None)))
    label.bind(texture_size=lambda w, val: setattr(label, "height", val[1]))
    scroll.add_widget(label)
    return scroll


class BBApp(App):
    def build(self):
        self.title = "BB V4"
        try:
            from gui import BBUI
            from brain import process
            return BBUI(process)
        except Exception:
            return _build_error_screen("STARTUP ERROR — screenshot this:\n\n" + traceback.format_exc())


if __name__ == "__main__":
    BBApp().run()
