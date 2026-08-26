import math
import random
import datetime
import traceback

from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Ellipse, Line, PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock
from settings import get_setting
from voice import speak, start_listening, start_always_listening, stop_always_listening
from bb_notify import register as register_notifier
# --- Futuristic dark theme palette ---
BG_COLOR = (0.02, 0.03, 0.05, 1)
ACCENT = (0.16, 0.85, 0.95, 1)          # electric cyan — idle / speaking
ACCENT_DIM = (0.10, 0.45, 0.50, 1)
LISTEN_COLOR = (1.0, 0.30, 0.42, 1)     # pink/red — listening
THINK_COLOR = (1.0, 0.70, 0.13, 1)      # amber — thinking
PANEL_COLOR = (0.05, 0.07, 0.10, 1)
TEXT_COLOR = (0.80, 0.95, 0.98, 1)

Window.clearcolor = BG_COLOR

STATE_COLORS = {
    "idle": ACCENT[:3],
    "listening": LISTEN_COLOR[:3],
    "thinking": THINK_COLOR[:3],
    "speaking": ACCENT[:3],
}
STATE_SPEED = {"idle": 1.0, "listening": 2.2, "thinking": 1.6, "speaking": 1.8}


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


...
class BBUI(BoxLayout):
    def __init__(self, callback, **kwargs):
        ...
        register_notifier(self._on_async_notify)

    def _on_async_notify(self, msg):
        def update(dt):
            self._append_chat(f"\n\n[color=2ad9f2]BB:[/color] {msg}")
            self._set_status("SYSTEM ONLINE", "2ad9f2", "idle")
        Clock.schedule_once(update, 0)


class HUDCore(Widget):
    """
    Animated AI core — pulsing glow center, two counter-rotating
    segmented rings, a slow ring of orbiting particles, and a live
    waveform strip along the bottom. Everything is drawn with plain
    canvas instructions (no images/shaders) at ~30fps, so it stays
    lightweight on low-end devices.

    Call set_state("idle" | "listening" | "thinking" | "speaking") to
    drive color + animation speed.
    """

    

    def set_state(self, state):
        self.state = state

    def _tick(self, dt):
        self._t += dt
        listening = self.state == "listening"

        for p in self._particles:
            p["angle"] = (p["angle"] + p["speed"] * dt * (2 if listening else 1)) % 360

        for i in range(len(self._wave_levels)):
            target = random.uniform(0.1, 1.0) if listening else 0.12
            rate = 0.5 if listening else 0.1
            self._wave_levels[i] += (target - self._wave_levels[i]) * rate

        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return

        cx = self.center_x
        cy = self.center_y + self.height * 0.08
        base_r = min(self.width, self.height) * 0.30

        color = STATE_COLORS.get(self.state, ACCENT)
        speed_mult = STATE_SPEED.get(self.state, 1.0)

        with self.canvas:
            # --- orbiting particles ---
            Color(*color, 0.55)
            for p in self._particles:
                rad = math.radians(p["angle"])
                pr = base_r * 1.9 + p["r_offset"]
                px = cx + pr * math.cos(rad)
                py = cy + pr * math.sin(rad)
                Ellipse(pos=(px - 2, py - 2), size=(4, 4))

            # --- counter-rotating segmented rings ---
            for ring_i, (radius_mult, seg_count, width) in enumerate([(1.55, 10, 2.2), (1.25, 16, 1.6)]):
                PushMatrix()
                angle = (self._t * 30 * speed_mult * (1 if ring_i == 0 else -1)) % 360
                Rotate(angle=angle, origin=(cx, cy))
                Color(*color, 0.75 if ring_i == 0 else 0.45)
                r = base_r * radius_mult
                gap = 360 / seg_count
                for s in range(seg_count):
                    start = s * gap
                    end = start + gap * 0.6
                    Line(circle=(cx, cy, r, start, end), width=width)
                PopMatrix()

            # --- pulsing glow core ---
            if self.state == "listening":
                pulse = 1.0 + 0.25 * abs(math.sin(self._t * 6))
            elif self.state == "thinking":
                pulse = 1.0 + 0.12 * abs(math.sin(self._t * 3))
            elif self.state == "speaking":
                pulse = 1.0 + 0.18 * abs(math.sin(self._t * 8))
            else:
                pulse = 1.0 + 0.06 * abs(math.sin(self._t * 1.4))

            for layer, alpha in [(1.6, 0.06), (1.15, 0.14), (0.8, 0.30)]:
                Color(*color, alpha)
                rr = base_r * layer * pulse
                Ellipse(pos=(cx - rr, cy - rr), size=(rr * 2, rr * 2))

            Color(*color, 0.9)
            core_r = base_r * 0.42 * pulse
            Ellipse(pos=(cx - core_r, cy - core_r), size=(core_r * 2, core_r * 2))

            # --- waveform strip along the bottom ---
            bar_count = len(self._wave_levels)
            total_w = self.width * 0.7
            bar_w = total_w / bar_count * 0.6
            gap_w = total_w / bar_count
            start_x = cx - total_w / 2
            base_y = self.y + self.height * 0.06
            max_h = self.height * 0.14

            Color(*color, 0.8)
            for i, level in enumerate(self._wave_levels):
                h = max(3, max_h * level)
                x = start_x + i * gap_w
                Rectangle(pos=(x, base_y), size=(bar_w, h))


class BBUI(BoxLayout):

    def __init__(self, callback, **kwargs):
        super().__init__(orientation="vertical", padding=16, spacing=10, **kwargs)

        self.callback = callback

        with self.canvas.before:
            Color(*BG_COLOR)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # --- Header: title + live clock/date ---
        header = BoxLayout(orientation="vertical", size_hint=(1, 0.10), spacing=2)

        self.title_label = Label(
            text="[b]B B   V 4[/b]",
            markup=True,
            halign="left",
            valign="top",
            color=ACCENT,
            font_size="18sp",
            size_hint=(1, 0.55)
        )
        self.title_label.bind(size=lambda w, s: setattr(w, "text_size", s))

        self.clock_label = Label(
            text="",
            halign="left",
            valign="top",
            color=(0.5, 0.7, 0.75, 1),
            font_size="12sp",
            size_hint=(1, 0.45)
        )
        self.clock_label.bind(size=lambda w, s: setattr(w, "text_size", s))

        header.add_widget(self.title_label)
        header.add_widget(self.clock_label)
        self.add_widget(header)
        Clock.schedule_interval(self._update_clock, 1)
        self._update_clock(0)

        # --- Animated HUD core ---
        self.hud = HUDCore(size_hint=(1, 0.30))
        self.add_widget(self.hud)

        # --- Status indicator ---
        self.status = Label(
            text="[color=2ad9f2]● SYSTEM ONLINE[/color]",
            markup=True,
            size_hint=(1, 0.05),
            color=ACCENT,
            font_size="14sp"
        )
        self.add_widget(self.status)

        # --- Chat log (scrollable) ---
        self.chat = Label(
            text="Welcome Boss. All systems ready.",
            halign="left",
            valign="top",
            size_hint_y=None,
            color=TEXT_COLOR,
            markup=True
        )
        self.chat.bind(texture_size=self._on_chat_texture)

        self.chat_scroll = ScrollView(size_hint=(1, 0.38), do_scroll_x=False)
        self.chat_scroll.bind(width=self._update_chat_text_width)
        self.chat_scroll.add_widget(self.chat)
        self.add_widget(self.chat_scroll)

        # --- Input row ---
        self.input = TextInput(
            hint_text="Type a command...",
            multiline=False,
            size_hint=(1, 0.08),
            background_color=PANEL_COLOR,
            foreground_color=TEXT_COLOR,
            cursor_color=ACCENT,
            hint_text_color=(0.4, 0.5, 0.55, 1),
            padding=[12, 12, 12, 12]
        )
        self.input.bind(on_text_validate=self.send)
        self.add_widget(self.input)

        # --- Buttons ---
        buttons = GridLayout(cols=3, size_hint=(1, 0.09), spacing=12)

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
        register_notifier(self._on_async_notify)

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _update_clock(self, dt):
        now = datetime.datetime.now()
        self.clock_label.text = now.strftime("%I:%M %p") + "   " + now.strftime("%d %b %Y")

    def _update_chat_text_width(self, *args):
        self.chat.text_size = (self.chat_scroll.width, None)

    def _on_chat_texture(self, *args):
        self.chat.height = self.chat.texture_size[1]
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, "scroll_y", 0), 0)

    def _on_async_notify(self, msg):
        def update(dt):
            self._append_chat(f"\n\n[color=2ad9f2]BB:[/color] {msg}")
            self._set_status("SYSTEM ONLINE", "2ad9f2", "idle")
        Clock.schedule_once(update, 0)
    def _append_chat(self, text):
        self.chat.text += text

    def _set_status(self, text, color_hex="2ad9f2", hud_state="idle"):
        self.status.text = f"[color={color_hex}]● {text}[/color]"
        self.hud.set_state(hud_state)

    def send(self, *args):
        text = self.input.text.strip()

        if not text:
            return

        self._set_status("PROCESSING...", "ffb020", "thinking")
        try:
            reply = self.callback(text)
        except Exception:
            reply = "⚠️ ERROR:\n" + traceback.format_exc()
        self._append_chat(f"\n\n[color=888888]You:[/color] {text}\n[color=2ad9f2]BB:[/color] {reply}")
        self.input.text = ""

        if get_setting("voice_enabled"):
            self._set_status("SPEAKING...", "2ad9f2", "speaking")
            status = speak(reply)
            if status:
                self._append_chat(f"\n[color=666666]({status})[/color]")

        self._set_status("SYSTEM ONLINE", "2ad9f2", "idle")

    def voice_mode(self, *args):
        self._set_status("LISTENING...", "ff4d6d", "listening")
        self._append_chat("\n\n[color=2ad9f2]BB:[/color] 🎤 Listening...")
        start_listening(self._on_voice_result)

    def _on_voice_result(self, text, error):
        def update(dt):
            if error:
                self._append_chat(f"\n[color=666666](🎤 {error})[/color]")
                self._set_status("SYSTEM ONLINE", "2ad9f2", "idle")
                return

            if not text:
                self._set_status("SYSTEM ONLINE", "2ad9f2", "idle")
                return

            self._set_status("PROCESSING...", "ffb020", "thinking")
            try:
                reply = self.callback(text)
            except Exception:
                reply = "⚠️ ERROR:\n" + traceback.format_exc()
            self._append_chat(f"\n\n[color=888888]You (voice):[/color] {text}\n[color=2ad9f2]BB:[/color] {reply}")

            if get_setting("voice_enabled"):
                self._set_status("SPEAKING...", "2ad9f2", "speaking")
                status = speak(reply)
                if status:
                    self._append_chat(f"\n[color=666666]({status})[/color]")

            self._set_status("SYSTEM ONLINE", "2ad9f2", "idle")

        Clock.schedule_once(update, 0)

    def toggle_wake(self, *args):
        if not self._wake_on:
            self._wake_on = True
            self.wake_btn.text = "WAKE: ON"
            self._append_chat("\n\n[color=2ad9f2]BB:[/color] 👂 Wake mode on — say 'Hey BB' any time.")
            self._set_status("WAKE MODE ACTIVE", "2ad9f2", "idle")
            start_always_listening(self._on_wake_command, self._on_wake_state)
        else:
            self._wake_on = False
            self.wake_btn.text = "WAKE: OFF"
            stop_always_listening()
            self._append_chat("\n\n[color=2ad9f2]BB:[/color] 👂 Wake mode off.")
            self._set_status("SYSTEM ONLINE", "2ad9f2", "idle")

    def _on_wake_state(self, state):
        def update(dt):
            if not self._wake_on:
                return
            if state == "listening":
                self._set_status("LISTENING FOR 'HEY BB'...", "ff4d6d", "listening")
        Clock.schedule_once(update, 0)

    def _on_wake_command(self, command):
        def update(dt):
            if not command:
                return

            self._set_status("PROCESSING...", "ffb020", "thinking")
            try:
                reply = self.callback(command)
            except Exception:
                reply = "⚠️ ERROR:\n" + traceback.format_exc()
            self._append_chat(f"\n\n[color=888888]You (voice):[/color] {command}\n[color=2ad9f2]BB:[/color] {reply}")

            if get_setting("voice_enabled"):
                self._set_status("SPEAKING...", "2ad9f2", "speaking")
                status = speak(reply)
                if status:
                    self._append_chat(f"\n[color=666666]({status})[/color]")

            self._set_status("WAKE MODE ACTIVE" if self._wake_on else "SYSTEM ONLINE", "2ad9f2", "idle")

        Clock.schedule_once(update, 0)
