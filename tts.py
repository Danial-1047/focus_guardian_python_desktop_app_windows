import pyttsx3
import threading

class TTS:
    def __init__(self, rate=None, volume=None):
        # self.engine = pyttsx3.init()
        if rate:
            self.engine.setProperty('rate', rate)
        if volume:
            self.engine.setProperty('volume', volume)
        self._lock = threading.Lock()

    def say(self, text):
        # Non-blocking speaking
        def _speak():
            # print(f"[TTS] Speaking")
            with self._lock:
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 170)
                    engine.setProperty('volume', 1.0)
                    voices = engine.getProperty('voices')
                    if 0 <= 2 < len(voices):
                        engine.setProperty('voice', voices[2].id)
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e2:
                    print(f"[TTS Fatal Error: {e2}]")
        t = threading.Thread(target=_speak, daemon=True)
        t.start()
