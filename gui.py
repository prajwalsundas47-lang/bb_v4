from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from settings import get_setting
from voice import speak, start_listening


class BBUI(BoxLayout):

    def __init__(self, callback, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)

        self.callback = callback

        self.chat = Label(
            text="🤖 BB V4 Online\n\nWelcome Boss!",
            halign="left",
            valign="top",
            size_hint=(1, 0.8)
        )

        self.chat.bind(size=self.update_size)
        self.add_widget(self.chat)

        self.input = TextInput(
            hint_text="Type a command...",
            multiline=False,
            size_hint=(1, 0.1)
        )

        self.input.bind(on_text_validate=self.send)
        self.add_widget(self.input)

        buttons = GridLayout(
            cols=2,
            size_hint=(1, 0.1),
            spacing=10
        )

        self.mic = Button(text="🎤")
        self.mic.bind(on_press=self.voice_mode)
        buttons.add_widget(self.mic)

        self.send_btn = Button(text="Send")
        self.send_btn.bind(on_press=self.send)
        buttons.add_widget(self.send_btn)

        self.add_widget(buttons)

    def update_size(self, *args):
        self.chat.text_size = self.chat.size

    def send(self, *args):

        text = self.input.text.strip()

        if not text:
            return

        reply = self.callback(text)

        self.chat.text += f"\n\nYou: {text}\nBB: {reply}"

        self.input.text = ""

        if get_setting("voice_enabled"):
            status = speak(reply)
            if status:
                self.chat.text += f"\n({status})"

    def voice_mode(self, *args):
        self.chat.text += "\n\nBB: 🎤 Listening..."
        start_listening(self._on_voice_result)

    def _on_voice_result(self, text, error):
        def update(dt):
            if error:
                self.chat.text += f"\n(🎤 {error})"
                return

            if not text:
                return

            reply = self.callback(text)
            self.chat.text += f"\n\nYou (voice): {text}\nBB: {reply}"

            if get_setting("voice_enabled"):
                status = speak(reply)
                if status:
                    self.chat.text += f"\n({status})"

        Clock.schedule_once(update, 0)
