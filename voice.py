try:
    from jnius import autoclass, PythonJavaClass, java_method
    ANDROID = True
except ImportError:
    ANDROID = False

from kivy.clock import Clock


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


def _init_tts():
    """Lazily create the TTS engine the first time speak() is called."""
    global _tts_engine

    if not ANDROID or _tts_engine is not None:
        return

    activity = PythonActivity.mActivity
    listener = _TTSInitListener()
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


def stop_always_listening():
    _wake_active[0] = False

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
            PythonActivity.mActivity.runOnUiThread(_UIRunnable(_stop))
        except Exception:
            pass


def start_always_listening(on_wake_command):
    """
    Continuously listens in a loop (while BB is open on screen) for
    'hey bb' in what's said. Anything spoken right after the wake
    phrase is passed to on_wake_command as the command; if the wake
    phrase is said alone, on_wake_command(None) is called instead.

    Unlike start_listening() (one-shot, used by the MIC button), this
    creates a SINGLE SpeechRecognizer and reuses it for every cycle by
    calling startListening() again after each result — the standard,
    stable Android pattern. Destroying and recreating a fresh recognizer
    every cycle (an earlier approach) caused frequent
    ERROR_SERVER_DISCONNECTED and app crashes.

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
    activity = PythonActivity.mActivity

    def _handle_result(text, error):
        if not _wake_active[0]:
            return

        try:
            if text:
                lowered = text.lower()
                command = None

                for phrase in ("hey bb", "hey b b", "hey be be"):
                    if phrase in lowered:
                        idx = lowered.find(phrase) + len(phrase)
                        command = text[idx:].strip()
                        break
                else:
                    if lowered.startswith("bb "):
                        command = text[3:].strip()

                if command is not None:
                    on_wake_command(command if command else None)
        except Exception:
            pass

        if _wake_active[0]:
            _main_handler.postDelayed(_UIRunnable(_restart_listening), 400)

    listener = _RecognitionListener(_handle_result)

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
        except Exception:
            pass

    def _create_recognizer():
        try:
            recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            recognizer.setRecognitionListener(listener)
            _wake_recognizer[0] = recognizer
            recognizer.startListening(_build_intent())
        except Exception:
            pass

    activity.runOnUiThread(_UIRunnable(_create_recognizer))


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

        activity.runOnUiThread(_UIRunnable(_start))

        def _timeout_check(dt):
            _safe_on_result(
                None,
                "No response after 8s — check that Pydroid 3 has Microphone "
                "permission in Settings > Apps > Pydroid 3 > Permissions."
            )

        Clock.schedule_once(_timeout_check, 8)

    except Exception as e:
        _safe_on_result(None, f"Could not start voice input: {e}")
