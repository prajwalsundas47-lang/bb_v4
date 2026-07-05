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

    class _TTSInitListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
        __javacontext__ = "app"

        @java_method("(I)V")
        def onInit(self, status):
            global _tts_ready, _tts_failed

            if status == 0:  # TextToSpeech.SUCCESS
                _tts_engine.setLanguage(Locale.US)
                _tts_ready = True

                while _pending_speech:
                    queued_text = _pending_speech.pop(0)
                    try:
                        _tts_engine.speak(queued_text, 0, HashMap())
                    except Exception:
                        pass
            else:
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
            self.on_result(None, f"Recognition error (code {error}).")

        @java_method("(Landroid/os/Bundle;)V")
        def onResults(self, results):
            try:
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches is not None and matches.size() > 0:
                    self.on_result(matches.get(0), None)
                else:
                    self.on_result(None, "No speech detected.")
            except Exception as e:
                self.on_result(None, f"Could not read speech result: {e}")

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


def start_listening(on_result):
    """
    Starts Android's built-in speech recognizer in the background
    (no popup UI) and calls on_result(text, error) when done.
    On success: on_result("what they said", None)
    On failure: on_result(None, "reason it failed")
    Guaranteed to call on_result exactly once, even on unexpected errors
    or if the recognizer never responds at all.
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
