import asyncio

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100


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


ALARM_PATTERN = _generate_alarm_pattern()
PATTERN_DURATION = len(ALARM_PATTERN) / SAMPLE_RATE


async def play_alarm_until(should_stop) -> None:
    """Loops the alarm pattern until should_stop() returns True."""
    check_interval = 0.5

    while not should_stop():
        sd.play(ALARM_PATTERN, SAMPLE_RATE)
        elapsed = 0.0

        while elapsed < PATTERN_DURATION:
            if should_stop():
                sd.stop()
                return

            await asyncio.sleep(check_interval)
            elapsed += check_interval

    sd.stop()
