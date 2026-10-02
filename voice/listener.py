import json
import queue

import numpy as np
import sounddevice as sd
import vosk

from voice.wake_phrases import ALL_WAKE_PHRASES

vosk.SetLogLevel(-1)

# What Vosk's model expects the audio to be, regardless of hardware.
MODEL_SAMPLE_RATE = 16000


def _get_input_samplerate() -> int:
    # Mirrors automation/alarm_sound.py's reasoning: PortAudio's ALSA
    # backend talks to the hardware directly, so it can only open a
    # stream at a rate the device actually supports natively - a USB
    # mic/speakerphone combo that only does 48000 Hz will fail outright
    # if asked for 16000 Hz, even though that's what the Vosk model
    # wants. Capture at whatever rate the device actually supports and
    # downsample to 16000 Hz in software instead of assuming it'll work.
    return int(sd.query_devices(kind="input")["default_samplerate"])

# Constrains recognition to this fixed phrase list instead of open-ended
# transcription, since Vosk's grammar mode is far more accurate for a small
# set of known commands than free dictation. "[unk]" lets it reject speech
# that doesn't match any of them instead of forcing the closest guess.
LAMP_COMMAND_PHRASES = [
    "turn on the desk lamp",
    "turn off the desk lamp",
    "turn on the cabinet lamp",
    "turn off the cabinet lamp",
    "turn on both lamps",
    "turn off both lamps",
    "lamps on",
    "lights on",
    "kill the lights",
    "lamps off",
    "lights off",
]

COMMAND_PHRASES = LAMP_COMMAND_PHRASES + ALL_WAKE_PHRASES


class VoiceListener:
    """Listens on the default microphone and recognizes COMMAND_PHRASES."""

    def __init__(self, model_path: str) -> None:
        model = vosk.Model(model_path)
        grammar = json.dumps(COMMAND_PHRASES + ["[unk]"])
        self.recognizer = vosk.KaldiRecognizer(model, MODEL_SAMPLE_RATE, grammar)

        self.device_samplerate = _get_input_samplerate()

        if self.device_samplerate % MODEL_SAMPLE_RATE != 0:
            raise RuntimeError(
                f"Input device sample rate ({self.device_samplerate}) isn't a "
                f"whole multiple of {MODEL_SAMPLE_RATE}; simple decimation "
                "won't work for this device."
            )

        self._downsample_ratio = self.device_samplerate // MODEL_SAMPLE_RATE

        self.commands: queue.Queue[str] = queue.Queue()
        self._stream = None

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if self._downsample_ratio > 1:
            samples = np.frombuffer(indata, dtype=np.int16)
            # Trim to a whole number of groups before reshaping, in case
            # this block's frame count isn't an exact multiple (can
            # happen on the last block of a stream).
            usable_len = len(samples) - (len(samples) % self._downsample_ratio)
            samples = samples[:usable_len].reshape(-1, self._downsample_ratio)
            downsampled = samples.mean(axis=1).astype(np.int16)
            audio_bytes = downsampled.tobytes()
        else:
            audio_bytes = bytes(indata)

        if self.recognizer.AcceptWaveform(audio_bytes):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()

            if text and text != "[unk]":
                self.commands.put(text)

    def start(self) -> None:
        block_seconds = 0.5
        blocksize = int(self.device_samplerate * block_seconds)

        self._stream = sd.RawInputStream(
            samplerate=self.device_samplerate,
            blocksize=blocksize,
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
