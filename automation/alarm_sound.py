import asyncio
import wave
from pathlib import Path

import numpy as np

# Playing this through sounddevice/PortAudio directly conflicts with the
# voice listener's already-open microphone stream when both end up on the
# same physical device (this USB speakerphone has a built-in mic too) -
# PortAudio's ALSA backend can't open a second raw stream on that hardware
# while the first is active. Writing a WAV file and playing it via pw-play
# goes through PipeWire's normal client mixing instead, the same way
# espeak-ng (a separate process) already coexists with the open mic stream.
SAMPLE_RATE = 44100
ALARM_TONE_PATH = Path(__file__).parent / "alarm_tone.wav"


def _generate_alarm_pattern() -> np.ndarray:
    beep_freq = 880
    beep_duration = 0.3
    gap_duration = 0.15
    beeps_per_group = 3
    group_gap_duration = 0.6

    t = np.linspace(0, beep_duration, int(SAMPLE_RATE * beep_duration), endpoint=False)
    beep = 0.5 * np.sin(2 * np.pi * beep_freq * t)

    # Fade the edges so each beep doesn't click.
    fade_samples = int(SAMPLE_RATE * 0.01)
    envelope = np.ones_like(beep)
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    beep *= envelope

    gap = np.zeros(int(SAMPLE_RATE * gap_duration))
    group_gap = np.zeros(int(SAMPLE_RATE * group_gap_duration))

    group = np.concatenate([beep, gap] * beeps_per_group)
    pattern = np.concatenate([group, group_gap])
    return pattern.astype(np.float32)


def _write_alarm_tone_wav() -> None:
    pattern = _generate_alarm_pattern()
    pcm16 = (np.clip(pattern, -1.0, 1.0) * 32767).astype(np.int16)

    with wave.open(str(ALARM_TONE_PATH), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm16.tobytes())


_write_alarm_tone_wav()


async def play_alarm_until(should_stop) -> None:
    """Loops the alarm tone via pw-play until should_stop() returns True."""
    check_interval = 0.5

    while not should_stop():
        process = await asyncio.create_subprocess_exec(
            "pw-play",
            str(ALARM_TONE_PATH),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        while True:
            try:
                await asyncio.wait_for(process.wait(), timeout=check_interval)
                break
            except asyncio.TimeoutError:
                if should_stop():
                    process.terminate()
                    await process.wait()
                    return
