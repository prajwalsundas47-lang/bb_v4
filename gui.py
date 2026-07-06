import traceback
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from settings import get_setting
from voice import speak, start_listening, start_always_listening, stop_always_listening

# --- Futuristic dark theme palette ---
BG_COLOR = (0.02, 0.03, 0.05, 1)
ACCENT = (0.16, 0.85, 0.95, 1)          # electric cyan
ACCENT_DIM = (0.10, 0.45, 0.50, 1)
PANEL_COLOR = (0.05, 0.07, 0.10, 1)
TEXT_COLOR = (0.80, 0.95, 0.98, 1)

Window.clearcolor = BG_COLOR


class GlowButton(Button):
    """A flat, cyan-accented button matching the HUD theme."""

    def __init__(self, **kwargs):
        super().__init__(
            background_normal="",
            background_down="",
            background_color=ACCENT_DIM,
            color=(0, 0, 0, 1),
            bold=True,
            **kwargs
        )


class BBUI(BoxLayout):

    def __init__(self, callback, **kwargs):
        super().__init__(orientation="vertical", padding=16, spacing=12, **kwargs)

        self.callback = callback

        with self.canvas.before:
            Color(*BG_COLOR)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # --- Header / status bar ---
        self.status = Label(
            text="[b]B B   V 4[/b]\n[color=2ad9f2]● SYSTEM ONLINE[/color]",
            markup=True,
            halign="left",
            valign="top",
            size_hint=(1, 0.12),
            color=ACCENT,
            font_size="20sp"
        )
        self.status.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.add_widget(self.status)

        # --- Chat log (now properly scrollable) ---
        self.chat = Label(
            text="Welcome Boss. All systems ready.",
            halign="left",
            valign="top",
            size_hint_y=None,
            color=TEXT_COLOR,
            markup=True
        )
        self.chat.bind(texture_size=self._on_chat_texture)

        self.chat_scroll = ScrollView(size_hint=(1, 0.68), do_scroll_x=False)
        self.chat_scroll.bind(width=self._update_chat_text_width)
        self.chat_scroll.add_widget(self.chat)
        self.add_widget(self.chat_scroll)

        # --- Input row ---
        self.input = TextInput(
            hint_text="Type a command...",
            multiline=False,
            size_hint=(1, 0.1),
            background_color=PANEL_COLOR,
            foreground_color=TEXT_COLOR,
            cursor_color=ACCENT,
            hint_text_color=(0.4, 0.5, 0.55, 1),
            padding=[12, 12, 12, 12]
        )
        self.input.bind(on_text_validate=self.send)
        self.add_widget(self.input)

        # --- Buttons ---
        buttons = GridLayout(cols=3, size_hint=(1, 0.1), spacing=12)

        self.mic = GlowButton(text="MIC")
        self.mic.bind(on_press=self.voice_mode)
        buttons.add_widget(self.mic)

        self.send_btn = GlowButton(text="SEND")
        self.send_btn.bind(on_press=self.send)
        buttons.add_widget(self.send_btn)

        self._wake_on = False
        self.wake_btn = GlowButton(text="WAKE: OFF")
        self.wake_btn.bind(on_press=self.toggle_wake)
        buttons.add_widget(self.wake_btn)

        self.add_widget(buttons)

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _update_chat_text_width(self, *args):
        # Wrap text to the scroll view's width so it doesn't run off-screen
        self.chat.text_size = (self.chat_scroll.width, None)

    def _on_chat_texture(self, *args):
        # Grow the label to fit its text, then keep the newest line visible
        self.chat.height = self.chat.texture_size[1]
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, "scroll_y", 0), 0)

    def _append_chat(self, text):
        self.chat.text += text

    def _set_status(self, text, color_hex="2ad9f2"):
        self.status.text = f"[b]B B   V 4[/b]\n[color={color_hex}]● {text}[/color]"

    def send(self, *args):
        text = self.input.text.strip()

        if not text:
            return

        self._set_status("PROCESSING...", "ffb020")
        try:
            reply = self.callback(text)
        except Exception:
            reply = "⚠️ ERROR:\n" + traceback.format_exc()
        self._append_chat(f"\n\n[color=888888]You:[/color] {text}\n[color=2ad9f2]BB:[/color] {reply}")
        self.input.text = ""
        self._set_status("SYSTEM ONLINE")

        if get_setting("voice_enabled"):
            status = speak(reply)
            if status:
                self._append_chat(f"\n[color=666666]({status})[/color]")

    def voice_mode(self, *args):
        self._set_status("LISTENING...", "ff4d6d")
        self._append_chat("\n\n[color=2ad9f2]BB:[/color] 🎤 Listening...")
        start_listening(self._on_voice_result)

    def _on_voice_result(self, text, error):
        def update(dt):
            if error:
                self._append_chat(f"\n[color=666666](🎤 {error})[/color]")
                self._set_status("SYSTEM ONLINE")
                return

            if not text:
                self._set_status("SYSTEM ONLINE")
                return

            self._set_status("PROCESSING...", "ffb020")
            try:
                reply = self.callback(text)
            except Exception:
                reply = "⚠️ ERROR:\n" + traceback.format_exc()
            self._append_chat(f"\n\n[color=888888]You (voice):[/color] {text}\n[color=2ad9f2]BB:[/color] {reply}")
            self._set_status("SYSTEM ONLINE")

            if get_setting("voice_enabled"):
                status = speak(reply)
                if status:
                    self._append_chat(f"\n[color=666666]({status})[/color]")

        Clock.schedule_once(update, 0)

    def toggle_wake(self, *args):
        if not self._wake_on:
            self._wake_on = True
            self.wake_btn.text = "WAKE: ON"
            self._append_chat("\n\n[color=2ad9f2]BB:[/color] 👂 Wake mode on — say 'Hey BB' any time.")
            self._set_status("WAKE MODE ACTIVE")
            start_always_listening(self._on_wake_command)
        else:
            self._wake_on = False
            self.wake_btn.text = "WAKE: OFF"
            stop_always_listening()
            self._append_chat("\n\n[color=2ad9f2]BB:[/color] 👂 Wake mode off.")
            self._set_status("SYSTEM ONLINE")

    def _on_wake_command(self, command):
        def update(dt):
            if not command:
                return

            try:
                reply = self.callback(command)
            except Exception:
                reply = "⚠️ ERROR:\n" + traceback.format_exc()
            self._append_chat(f"\n\n[color=888888]You (voice):[/color] {command}\n[color=2ad9f2]BB:[/color] {reply}")

            if get_setting("voice_enabled"):
                status = speak(reply)
                if status:
                    self._append_chat(f"\n[color=666666]({status})[/color]")

        Clock.schedule_once(update, 0)
