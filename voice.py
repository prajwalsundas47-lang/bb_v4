try:
    from jnius import autoclass, PythonJavaClass, java_method
    ANDROID = True
except ImportError:
    ANDROID = False

import difflib
from kivy.clock import Clock


# Android's speech recognizer very commonly mishears the short wake word
# "bb" as a similar-sounding real word ("baby", "bebe", "abby", ...).
# Matching only exact phrases (as before) meant wake mode silently failed
# almost every time. Instead, fuzzy-match the word(s) right after a
# greeting ("hey"/"hi"/"hello") against known variants.
_WAKE_VARIANTS = ("bb", "b b", "be be", "baby", "bebe", "abby", "bebi", "beebee")
_GREETING_WORDS = ("hey", "hi", "hello", "ok", "okay")


def _match_wake_word(word):
    word = word.strip(",.!?").lower()
    if not word:
        return False
    for variant in _WAKE_VARIANTS:
        if difflib.SequenceMatcher(None, word, variant).ratio() >= 0.6:
            return True
    return False


def _extract_wake_command(text):
    """
    Returns the command text following a wake phrase, or None if no
    wake phrase was detected anywhere in `text`.
    """
    words = text.lower().split()
    if not words:
        return None

    if words[0] in _GREETING_WORDS and len(words) > 1:
        if _match_wake_word(words[1]):
            return " ".join(words[2:]).strip()
        if len(words) > 2 and _match_wake_word(words[1] + words[2]):
            return " ".join(words[3:]).strip()
    elif _match_wake_word(words[0]):
        return " ".join(words[1:]).strip()

    return None


_tts_engine = None
_tts_ready = False
_tts_failed = False
_pending_speech = []


if ANDROID:
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
    Locale = autoclass("java.util.Locale")
    HashMap = autoclass("java.util.HashMap")
    SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")
    RecognizerIntent = autoclass("android.speech.RecognizerIntent")
    Intent = autoclass("android.content.Intent")
    Handler = autoclass("android.os.Handler")
    Looper = autoclass("android.os.Looper")
    _main_handler = Handler(Looper.getMainLooper())

    class _TTSInitListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
        __javacontext__ = "app"

        @java_method("(I)V")
        def onInit(self, status):
            global _tts_ready, _tts_failed

            try:
                if status == 0:  # TextToSpeech.SUCCESS
                    _tts_engine.setLanguage(Locale.US)

                    try:
                        voices = _tts_engine.getVoices()
                        if voices is not None:
                            iterator = voices.iterator()
                            while iterator.hasNext():
                                voice = iterator.next()
                                name = voice.getName().lower()
                                if "female" in name:
                                    _tts_engine.setVoice(voice)
                                    break
                    except Exception:
                        pass

                    _tts_ready = True

                    while _pending_speech:
                        queued_text = _pending_speech.pop(0)
                        try:
                            _tts_engine.speak(queued_text, 0, HashMap())
                        except Exception:
                            pass
                else:
                    _tts_failed = True
            except Exception:
                _tts_failed = True

    class _UIRunnable(PythonJavaClass):
        __javainterfaces__ = ["java/lang/Runnable"]
        __javacontext__ = "app"

        def __init__(self, func):
            super().__init__()
            self.func = func

        @java_method("()V")
        def run(self):
            try:
                self.func()
            except Exception:
                pass

    class _RecognitionListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/RecognitionListener"]
        __javacontext__ = "app"

        def __init__(self, on_result):
            super().__init__()
            self.on_result = on_result

        @java_method("(Landroid/os/Bundle;)V")
        def onReadyForSpeech(self, params):
            pass

        @java_method("()V")
        def onBeginningOfSpeech(self):
            pass

        @java_method("(F)V")
        def onRmsChanged(self, rmsdB):
            pass

        @java_method("([B)V")
        def onBufferReceived(self, buffer):
            pass

        @java_method("()V")
        def onEndOfSpeech(self):
            pass

        @java_method("(I)V")
        def onError(self, error):
            try:
                self.on_result(None, f"Recognition error (code {error}).")
            except Exception:
                pass

        @java_method("(Landroid/os/Bundle;)V")
        def onResults(self, results):
            try:
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches is not None and matches.size() > 0:
                    self.on_result(matches.get(0), None)
                else:
                    self.on_result(None, "No speech detected.")
            except Exception as e:
                try:
                    self.on_result(None, f"Could not read speech result: {e}")
                except Exception:
                    pass

        @java_method("(Landroid/os/Bundle;)V")
        def onPartialResults(self, partialResults):
            pass

        @java_method("(ILandroid/os/Bundle;)V")
        def onEvent(self, eventType, params):
            pass


_pinned_runnables = []  # keeps EVERY runnable alive forever — cheap, avoids
                         # the exact GC-crash pattern we just found for listeners


def _make_runnable(func):
    r = _UIRunnable(func)
    _pinned_runnables.append(r)
    return r


_tts_listener_ref = [None]


def _init_tts():
    """Lazily create the TTS engine the first time speak() is called."""
    global _tts_engine

    if not ANDROID or _tts_engine is not None:
        return

    activity = PythonActivity.mActivity
    listener = _TTSInitListener()
    _tts_listener_ref[0] = listener  # same GC-safety fix as the recognizer listeners
    _tts_engine = TextToSpeech(activity, listener)


def speak(text):
    """
    Speak text out loud using Android's built-in TTS engine.
    Returns None on success, or a short status string if BB couldn't
    speak yet (so the caller can show it in chat for debugging).
    """
    if not ANDROID:
        return "Voice output is not available on this device."

    _init_tts()

    if _tts_failed:
        return "⚠️ TTS engine failed to start. Check Settings > Accessibility > Text-to-speech output."

    if not _tts_ready or _tts_engine is None:
        _pending_speech.append(text)
        return "🔇 Voice engine still starting — it'll speak the next reply."

    try:
        _tts_engine.speak(text, 0, HashMap())
        return None
    except Exception as e:
        return f"Could not speak: {e}"


_wake_active = [False]
_wake_recognizer = [None]
_wake_listener_ref = [None]  # MUST stay referenced — see crash notes below
_one_shot_listener_ref = [None]  # same, for the MIC-button path
_wake_state_callback = [None]  # optional: gui.py's HUD state updater


def _notify_wake_state(state):
    cb = _wake_state_callback[0]
    if cb is not None:
        try:
            cb(state)
        except Exception:
            pass


def stop_always_listening():
    _wake_active[0] = False
    _wake_listener_ref[0] = None
    _wake_state_callback[0] = None

    if ANDROID and _wake_recognizer[0] is not None:
        recognizer = _wake_recognizer[0]
        _wake_recognizer[0] = None

        def _stop():
            try:
                recognizer.stopListening()
            except Exception:
                pass
            try:
                recognizer.destroy()
            except Exception:
                pass

        try:
            PythonActivity.mActivity.runOnUiThread(_make_runnable(_stop))
        except Exception:
            pass


def start_always_listening(on_wake_command, on_state_change=None):
    """
    Continuously listens in a loop (while BB is open on screen) for
    'hey bb' in what's said. Anything spoken right after the wake
    phrase is passed to on_wake_command as the command; if the wake
    phrase is said alone, on_wake_command(None) is called instead.

    on_state_change, if given, is called with "listening" each time a
    fresh listen cycle actually starts (mic is live) — lets gui.py
    drive the HUD's pulsing "listening" animation instead of sitting
    on a static "wake mode active" state between cycles.

    Unlike start_listening() (one-shot, used by the MIC button), this
    creates a SINGLE SpeechRecognizer and reuses it for every cycle by
    calling startListening() again after each result — the standard,
    stable Android pattern.

    Note: this only runs while the BB app itself is open/foreground.
    Surviving the app being minimized or the screen locked needs a
    real persistent Android background service — a separate, bigger
    project.
    """
    if not ANDROID:
        on_wake_command(None)
        return

    if _wake_active[0]:
        return

    _wake_active[0] = True
    _wake_state_callback[0] = on_state_change
    activity = PythonActivity.mActivity

    def _handle_result(text, error):
        if not _wake_active[0]:
            return

        try:
            if text:
                command = _extract_wake_command(text)

                if command is not None:
                    on_wake_command(command if command else None)
        except Exception:
            pass

        if _wake_active[0]:
            _main_handler.postDelayed(_make_runnable(_restart_listening), 400)

    listener = _RecognitionListener(_handle_result)
    _wake_listener_ref[0] = listener  # CRITICAL: prevents Python GC from
    # freeing this object while Java's SpeechRecognizer still holds a
    # reference and calls back into it — confirmed root cause of the
    # SIGSEGV null-pointer crash (via adb logcat: crash happened inside
    # org.jnius.NativeInvocationHandler.invoke while Android's
    # SpeechRecognizerImpl tried to deliver a callback).

    def _build_intent():
        intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toString())
        return intent

    def _restart_listening():
        if not _wake_active[0] or _wake_recognizer[0] is None:
            return
        try:
            _wake_recognizer[0].startListening(_build_intent())
            _notify_wake_state("listening")
        except Exception:
            pass

    def _create_recognizer():
        try:
            recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            recognizer.setRecognitionListener(listener)
            _wake_recognizer[0] = recognizer
            recognizer.startListening(_build_intent())
            _notify_wake_state("listening")
        except Exception:
            pass

    activity.runOnUiThread(_make_runnable(_create_recognizer))


def start_listening(on_result):
    """
    One-shot: starts Android's built-in speech recognizer, calls
    on_result(text, error) once, then the recognizer is destroyed.
    Used by the MIC button (as opposed to start_always_listening,
    which is the continuous WAKE-mode loop).
    """
    if not ANDROID:
        on_result(None, "Voice input is not available on this device.")
        return

    result_given = [False]

    def _safe_on_result(text, error):
        if result_given[0]:
            return
        result_given[0] = True
        on_result(text, error)

    try:
        activity = PythonActivity.mActivity

        if not SpeechRecognizer.isRecognitionAvailable(activity):
            _safe_on_result(None, "Speech recognition isn't available on this device.")
            return

        listener = _RecognitionListener(_safe_on_result)
        _one_shot_listener_ref[0] = listener  # keep alive until result arrives

        def _start():
            try:
                recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
                recognizer.setRecognitionListener(listener)

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toString())

                recognizer.startListening(intent)
            except Exception as e:
                _safe_on_result(None, f"Could not start voice input: {e}")

        activity.runOnUiThread(_make_runnable(_start))

        def _timeout_check(dt):
            _safe_on_result(
                None,
                "No response after 8s — check that Pydroid 3 has Microphone "
                "permission in Settings > Apps > Pydroid 3 > Permissions."
            )

        Clock.schedule_once(_timeout_check, 8)

    except Exception as e:
        _safe_on_result(None, f"Could not start voice input: {e}")

_conversation_active = [False]


def start_conversation_mode(on_turn, on_state_change=None):
    """
    True back-and-forth voice conversation: after the wake word starts
    it, BB listens, you speak, it replies (spoken), then IMMEDIATELY
    listens again — no repeated wake word needed — until you say
    "stop conversation" / "that's all" / 10s of silence.
    on_turn(text) is called with what was heard each turn.
    """
    if not ANDROID:
        return
    _conversation_active[0] = True
    _listen_next_turn(on_turn, on_state_change)


def _listen_next_turn(on_turn, on_state_change):
    if not _conversation_active[0]:
        return

    def _on_result(text, error):
        if not _conversation_active[0]:
            return
        if text:
            if text.lower().strip() in ("stop conversation", "that's all", "stop listening", "end conversation"):
                stop_conversation_mode()
                return
            on_turn(text)
        # Whether it heard something or timed out, keep the loop going
        # until the user explicitly stops it.
        _listen_next_turn(on_turn, on_state_change)

    start_listening(_on_result)
    if on_state_change:
        on_state_change("listening")


def stop_conversation_mode():
    _conversation_active[0] = False
