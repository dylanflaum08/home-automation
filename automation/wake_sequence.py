import json
from datetime import datetime, timedelta
from pathlib import Path

from voice.wake_phrases import WakeTimeSpec

STATE_PATH = Path(__file__).parent / "wake_state.json"


def compute_target_datetime(spec: WakeTimeSpec, now: datetime) -> datetime:
    period = spec.period or "am"
    day = spec.day or "tomorrow"

    if period == "am":
        hour_24 = 0 if spec.hour == 12 else spec.hour
    else:
        hour_24 = 12 if spec.hour == 12 else spec.hour + 12

    target_date = now.date()

    if day == "tomorrow":
        target_date += timedelta(days=1)

    target_dt = datetime.combine(target_date, datetime.min.time())
    target_dt = target_dt.replace(hour=hour_24, minute=spec.minute)

    # If "today" was said (or implied) but that time has already passed,
    # treat it the way a phone alarm would rather than schedule something
    # that can never fire.
    if target_dt <= now:
        target_dt += timedelta(days=1)

    return target_dt


def save_wake_sequence(target_dt: datetime) -> None:
    STATE_PATH.write_text(json.dumps({"target": target_dt.isoformat()}))


def load_wake_sequence() -> datetime | None:
    if not STATE_PATH.exists():
        return None

    try:
        data = json.loads(STATE_PATH.read_text())
        return datetime.fromisoformat(data["target"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def clear_wake_sequence() -> None:
    STATE_PATH.unlink(missing_ok=True)
