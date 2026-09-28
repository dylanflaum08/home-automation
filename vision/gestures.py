from enum import Enum
from math import hypot


class PointDirection(Enum):
    NONE = "none"
    LEFT = "left"
    RIGHT = "right"


class HandCommand(Enum):
    NONE = "none"
    OPEN = "open"
    FIST = "fist"


class GlobalGesture(Enum):
    NONE = "none"
    PRAYER = "prayer"


def finger_is_extended(landmarks, tip: int, pip: int) -> bool:
    """Check whether a non-thumb finger is extended."""
    return landmarks[tip].y < landmarks[pip].y


def distance_between_points(point_a, point_b) -> float:
    return hypot(
        point_a.x - point_b.x,
        point_a.y - point_b.y,
    )


def index_finger_is_straight(landmarks) -> bool:
    """
    Orientation-independent check for whether the index finger is
    extended, using distance from the knuckle rather than tip.y < pip.y.

    A pointing finger can aim in any direction - left, right, level, or
    down - not just upward, so a vertical-only comparison misses level
    or downward points entirely.
    """
    index_mcp = landmarks[5]
    index_pip = landmarks[6]
    index_tip = landmarks[8]

    tip_distance = distance_between_points(index_tip, index_mcp)
    pip_distance = distance_between_points(index_pip, index_mcp)

    return tip_distance > pip_distance * 1.8


def finger_is_curled(landmarks, mcp: int, pip: int, tip: int) -> bool:
    """
    Orientation-independent check for whether a finger is curled toward
    the palm, using the same distance-from-knuckle idea as
    index_finger_is_straight but inverted.

    finger_is_extended's tip.y < pip.y check only requires the tip to not
    be pointing upward - a relaxed, half-open resting hand (e.g. hovering
    over a keyboard) satisfies that just as easily as a real fist, which
    let ordinary hand positions get misread as the "other fingers folded"
    half of a pointing gesture. Requiring the tip to actually be close to
    the knuckle demands real curling, not just "not upward."
    """
    mcp_point = landmarks[mcp]
    pip_point = landmarks[pip]
    tip_point = landmarks[tip]

    tip_distance = distance_between_points(tip_point, mcp_point)
    pip_distance = distance_between_points(pip_point, mcp_point)

    return tip_distance < pip_distance * 1.3


def detect_point_direction(landmarks) -> PointDirection:
    """
    Detect a generally leftward or rightward pointing gesture.

    The index finger must be extended while the middle, ring,
    and pinky fingers are folded. The finger may angle somewhat
    upward or downward.
    """

    wrist = landmarks[0]
    index_mcp = landmarks[5]
    index_pip = landmarks[6]
    index_tip = landmarks[8]

    index_extended = index_finger_is_straight(landmarks)
    middle_folded = finger_is_curled(landmarks, 9, 10, 12)
    ring_folded = finger_is_curled(landmarks, 13, 14, 16)
    pinky_folded = finger_is_curled(landmarks, 17, 18, 20)

    if not (
        index_extended
        and middle_folded
        and ring_folded
        and pinky_folded
    ):
        return PointDirection.NONE

    # Use the direction of the index finger itself, rather than
    # comparing only the fingertip with the wrist.
    finger_dx = index_tip.x - index_mcp.x
    finger_dy = index_tip.y - index_mcp.y

    # Require meaningful sideways extension, relative to the finger's own
    # length rather than a fixed image-coordinate distance. A hand farther
    # from the camera occupies less of the frame, so its dx/dy are smaller
    # in absolute terms even for a fully sideways point - a fixed threshold
    # here made pointing fail whenever the hand wasn't close to the camera.
    finger_length = distance_between_points(index_tip, index_mcp)

    if finger_length == 0:
        return PointDirection.NONE

    minimum_horizontal_fraction = 0.35

    if abs(finger_dx) < finger_length * minimum_horizontal_fraction:
        return PointDirection.NONE

    # Allow the finger to slope substantially upward or downward.
    # A value of 2.2 means vertical movement can be up to 2.2 times
    # the horizontal movement and still count as sideways pointing.
    maximum_slope = 2.2

    if abs(finger_dy) > abs(finger_dx) * maximum_slope:
        return PointDirection.NONE

    if finger_dx < 0:
        return PointDirection.LEFT

    return PointDirection.RIGHT

def detect_hand_command(landmarks) -> HandCommand:
    """
    Open hand: four non-thumb fingers extended.
    Fist: four non-thumb fingers folded.
    """

    extended_count = sum(
        [
            finger_is_extended(landmarks, 8, 6),
            finger_is_extended(landmarks, 12, 10),
            finger_is_extended(landmarks, 16, 14),
            finger_is_extended(landmarks, 20, 18),
        ]
    )

    if extended_count == 4:
        return HandCommand.OPEN

    if extended_count == 0:
        return HandCommand.FIST

    return HandCommand.NONE


def hand_is_open_for_prayer(landmarks) -> bool:
    """
    Require the four main fingers to be extended for prayer hands.
    """

    extended_count = sum(
        [
            finger_is_extended(landmarks, 8, 6),
            finger_is_extended(landmarks, 12, 10),
            finger_is_extended(landmarks, 16, 14),
            finger_is_extended(landmarks, 20, 18),
        ]
    )

    return extended_count >= 3


def detect_prayer_hands(hand_a, hand_b) -> bool:
    """
    Detect two open hands pressed together.

    We compare palm centers, wrists, and fingertips so hands merely
    crossing each other do not trigger as easily.
    """

    if not (
        hand_is_open_for_prayer(hand_a)
        and hand_is_open_for_prayer(hand_b)
    ):
        return False

    palm_a = hand_a[9]
    palm_b = hand_b[9]

    wrist_a = hand_a[0]
    wrist_b = hand_b[0]

    middle_tip_a = hand_a[12]
    middle_tip_b = hand_b[12]

    palm_distance = distance_between_points(palm_a, palm_b)
    wrist_distance = distance_between_points(wrist_a, wrist_b)
    fingertip_distance = distance_between_points(
        middle_tip_a,
        middle_tip_b,
    )

    # The palms and fingers should be close together.
    palms_close = palm_distance < 0.13
    wrists_reasonably_close = wrist_distance < 0.22
    fingertips_close = fingertip_distance < 0.14

    # Prayer hands normally have fingertips above the wrists.
    hands_vertical = (
        middle_tip_a.y < wrist_a.y
        and middle_tip_b.y < wrist_b.y
    )

    return (
        palms_close
        and wrists_reasonably_close
        and fingertips_close
        and hands_vertical
    )


def detect_global_gesture(detected_hands) -> GlobalGesture:
    """
    Global gestures have priority over lamp-selection gestures.
    """

    if (
        len(detected_hands) >= 2
        and detect_prayer_hands(
            detected_hands[0],
            detected_hands[1],
        )
    ):
        return GlobalGesture.PRAYER

    return GlobalGesture.NONE