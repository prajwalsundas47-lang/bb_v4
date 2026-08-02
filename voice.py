try:
    from jnius import autoclass, PythonJavaClass, java_method
    ANDROID = True
except ImportError:
    ANDROID = False

from kivy.clock import Clock
from elevenlabs_tts import speak_elevenlabs


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
                self.on_result(None, f"Recognition error (code {error}).", error)
            except Exception:
                pass

        @java_method("(Landroid/os/Bundle;)V")
        def onResults(self, results):
            try:
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches is not None and matches.size() > 0:
                    self.on_result(matches.get(0), None, None)
                else:
                    self.on_result(None, "No speech detected.", None)
            except Exception as e:
                try:
                    self.on_result(None, f"Could not read speech result: {e}", None)
                except Exception:
                    pass

        @java_method("(Landroid/os/Bundle;)V")
        def onPartialResults(self, partialResults):
            pass

        @java_method("(ILandroid/os/Bundle;)V")
        def onEvent(self, eventType, params):
            pass


def _init_tts():
    """Lazily create the Android TTS engine the first time it's needed."""
    global _tts_engine

    if not ANDROID or _tts_engine is not None:
        return

    activity = PythonActivity.mActivity
    listener = _TTSInitListener()
    _tts_init_listener_holder[0] = listener  # keep alive — see GC-safety note above
    _tts_engine = TextToSpeech(activity, listener)


def _speak_android(text):
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


def speak(text):
    """
    Speak text out loud. Tries ElevenLabs first (higher quality voice);
    if no key is set or the request fails, transparently falls back to
    Android's built-in TTS so BB never goes silent.

    Returns None on success, or a short status string for debugging.
    """
    status = speak_elevenlabs(text)

    if status is None:
        return None  # ElevenLabs spoke successfully

    if status != "NO_KEY":
        # ElevenLabs was configured but failed (bad key/network) — still
        # fall back, but keep the reason visible for debugging.
        fallback_status = _speak_android(text)
        return f"(ElevenLabs: {status}) " + (fallback_status or "")

    return _speak_android(text)


# ---------------------------------------------------------------------
# Wake-word ("Hey BB") continuous listening
#
# Known issue: this loop has crashed at the native/JNI level on-device
# under some conditions. Two changes here reduce (but can't fully
# eliminate without a logcat trace) the chance of that happening:
#
#   1. A "busy" guard (_recognizer_busy) stops us from ever calling
#      startListening() on a recognizer that's already mid-listen —
#      double-starting a SpeechRecognizer is a common native crash
#      trigger, especially on Samsung's speech stack.
#   2. Exponential backoff + periodic recognizer recreation: instead of
#      always retrying after a flat 400ms, delay grows on repeated
#      errors, and after several consecutive errors the recognizer
#      object itself is destroyed and rebuilt (some devices leak native
#      state in the recognizer across many rapid cycles).
#
# If it still crashes the whole app (not just this feature), that's a
# native crash Python's try/except cannot catch — the only way to see
# the real cause is `adb logcat` at the moment of the crash.
# ---------------------------------------------------------------------

# --- GC-safety holders -------------------------------------------------
# CRITICAL: every jnius PythonJavaClass instance (listeners, runnables)
# MUST be kept referenced from Python for as long as Java might call back
# into it. If the only reference is a local variable, CPython's garbage
# collector can free the object while Java still holds a JNI reference to
# it — the next callback then crashes the native process instantly with
# SIGSEGV at fault addr 0x1. This is exactly what was happening here:
# a brand-new _UIRunnable was created every wake-loop cycle and had
# nothing keeping it alive between being scheduled and actually firing.
_tts_init_listener_holder = [None]
_wake_listener_holder = [None]
_wake_create_runnable_holder = [None]
_wake_restart_runnable_holder = [None]
_wake_recreate_runnable_holder = [None]
_oneshot_listener_holder = [None]
_oneshot_runnable_holder = [None]
# -------------------------------------------------------------------------

_wake_active = [False]
_wake_recognizer = [None]
_recognizer_busy = [False]
_error_streak = [0]

_BASE_DELAY_MS = 400
_MAX_DELAY_MS = 3000
_RECREATE_AFTER_ERRORS = 4


def stop_always_listening():
    _wake_active[0] = False
    _recognizer_busy[0] = False
    _error_streak[0] = 0

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
    Continuously listens (while BB is open on screen) for 'hey bb'.
    Anything spoken right after the wake phrase is passed to
    on_wake_command as the command; if the phrase is said alone,
    on_wake_command(None) is called instead.

    Only runs while the BB app itself is open/foreground — surviving
    minimize/lock needs a real background Android service (separate,
    bigger project).
    """
    if not ANDROID:
        on_wake_command(None)
        return

    if _wake_active[0]:
        return

    _wake_active[0] = True
    _error_streak[0] = 0
    activity = PythonActivity.mActivity

    def _handle_result(text, error, error_code):
        if not _wake_active[0]:
            return

        _recognizer_busy[0] = False

        if error:
            _error_streak[0] += 1
        else:
            _error_streak[0] = 0
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

        if not _wake_active[0]:
            return

        delay = min(_BASE_DELAY_MS * (_error_streak[0] + 1), _MAX_DELAY_MS)

        # Reuse the SAME persistent runnable objects every cycle instead
        # of creating a new one each time — see GC-safety note above.
        if _error_streak[0] >= _RECREATE_AFTER_ERRORS:
            _error_streak[0] = 0
            _main_handler.postDelayed(_wake_recreate_runnable_holder[0], delay)
        else:
            _main_handler.postDelayed(_wake_restart_runnable_holder[0], delay)

    listener = _RecognitionListener(_handle_result)
    _wake_listener_holder[0] = listener  # keep alive for the whole wake session

    def _build_intent():
        intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toString())
        return intent

    def _restart_listening():
        if not _wake_active[0] or _wake_recognizer[0] is None or _recognizer_busy[0]:
            return
        try:
            _recognizer_busy[0] = True
            _wake_recognizer[0].startListening(_build_intent())
        except Exception:
            _recognizer_busy[0] = False

    def _create_recognizer():
        if not _wake_active[0]:
            return
        try:
            recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            recognizer.setRecognitionListener(_wake_listener_holder[0])
            _wake_recognizer[0] = recognizer
            _recognizer_busy[0] = True
            recognizer.startListening(_build_intent())
        except Exception:
            _recognizer_busy[0] = False

    def _recreate_recognizer():
        if not _wake_active[0]:
            return
        old = _wake_recognizer[0]
        _wake_recognizer[0] = None
        _recognizer_busy[0] = False
        if old is not None:
            try:
                old.destroy()
            except Exception:
                pass
        _create_recognizer()

    # Create each runnable exactly ONCE per wake session and hold a
    # persistent reference — never build a fresh _UIRunnable per cycle.
    _wake_create_runnable_holder[0] = _UIRunnable(_create_recognizer)
    _wake_restart_runnable_holder[0] = _UIRunnable(_restart_listening)
    _wake_recreate_runnable_holder[0] = _UIRunnable(_recreate_recognizer)

    activity.runOnUiThread(_wake_create_runnable_holder[0])


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

    def _safe_on_result(text, error, error_code=None):
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
