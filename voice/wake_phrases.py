from collections import namedtuple

WakeTimeSpec = namedtuple("WakeTimeSpec", ["hour", "minute", "period", "day"])

HOUR_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
}

# 5-minute granularity keeps the generated grammar a manageable size and
# matches how people actually say alarm times ("six forty", not "six
# forty-three").
MINUTE_WORDS = {
    0: "o'clock",
    5: "five",
    10: "ten",
    15: "fifteen",
    20: "twenty",
    25: "twenty five",
    30: "thirty",
    35: "thirty five",
    40: "forty",
    45: "forty five",
    50: "fifty",
    55: "fifty five",
}

PERIODS = [None, "am", "pm"]
DAYS = [None, "today", "tomorrow"]


def _build_wake_phrase_map() -> dict[str, WakeTimeSpec]:
    phrase_map = {}

    for hour, hour_word in HOUR_WORDS.items():
        for minute, minute_word in MINUTE_WORDS.items():
            for period in PERIODS:
                for day in DAYS:
                    words = ["set", "wake", "up", "sequence", "for", hour_word, minute_word]

                    if period:
                        words.append(period)

                    if day:
                        words.append(day)

                    phrase = " ".join(words)
                    phrase_map[phrase] = WakeTimeSpec(hour, minute, period, day)

    return phrase_map


WAKE_PHRASE_MAP: dict[str, WakeTimeSpec] = _build_wake_phrase_map()
SET_WAKE_PHRASES: list[str] = list(WAKE_PHRASE_MAP.keys())

QUERY_WAKE_PHRASE = "query wake up sequence"
CANCEL_WAKE_PHRASE = "cancel wake up sequence"

ALL_WAKE_PHRASES: list[str] = SET_WAKE_PHRASES + [
    QUERY_WAKE_PHRASE,
    CANCEL_WAKE_PHRASE,
]


def format_wake_time_spec(spec: WakeTimeSpec) -> str:
    minute_word = MINUTE_WORDS[spec.minute]
    period = spec.period or "am"
    day = spec.day or "tomorrow"
    return f"{HOUR_WORDS[spec.hour]} {minute_word} {period} {day}"
