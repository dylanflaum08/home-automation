import json
import queue

import sounddevice as sd
import vosk

vosk.SetLogLevel(-1)

SAMPLE_RATE = 16000
BLOCK_SIZE = 8000

# Constrains recognition to this fixed phrase list instead of open-ended
# transcription, since Vosk's grammar mode is far more accurate for a small
# set of known commands than free dictation. "[unk]" lets it reject speech
# that doesn't match any of them instead of forcing the closest guess.
COMMAND_PHRASES = [
    "turn on the desk lamp",
    "turn off the desk lamp",
    "turn on the cabinet lamp",
    "turn off the cabinet lamp",
    "turn on both lamps",
    "turn off both lamps",
    "lumos",
    "lamps on",
    "kill the lights",
    "lamps off",
]


class VoiceListener:
    """Listens on the default microphone and recognizes COMMAND_PHRASES."""

    def __init__(self, model_path: str) -> None:
        model = vosk.Model(model_path)
        grammar = json.dumps(COMMAND_PHRASES + ["[unk]"])
        self.recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE, grammar)

        self.commands: queue.Queue[str] = queue.Queue()
        self._stream = None

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if self.recognizer.AcceptWaveform(bytes(indata)):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()

            if text and text != "[unk]":
                self.commands.put(text)

    def start(self) -> None:
        self._stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def get_command_nowait(self) -> str | None:
        try:
            return self.commands.get_nowait()
        except queue.Empty:
            return None
