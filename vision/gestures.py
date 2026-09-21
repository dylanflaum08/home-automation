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
    HANG_LOOSE = "hang_loose"


def finger_is_extended(landmarks, tip: int, pip: int) -> bool:
    """Check whether a non-thumb finger is extended."""
    return landmarks[tip].y < landmarks[pip].y


def distance_between_points(point_a, point_b) -> float:
    return hypot(
        point_a.x - point_b.x,
        point_a.y - point_b.y,
    )


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

    index_extended = finger_is_extended(landmarks, 8, 6)
    middle_folded = not finger_is_extended(landmarks, 12, 10)
    ring_folded = not finger_is_extended(landmarks, 16, 14)
    pinky_folded = not finger_is_extended(landmarks, 20, 18)

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

    # Require meaningful sideways extension.
    minimum_horizontal_extension = 0.07

    if abs(finger_dx) < minimum_horizontal_extension:
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


def thumb_is_extended(landmarks) -> bool:
    """
    Detect an extended thumb using distance from the palm.

    This works better than relying only on left/right orientation.
    """

    wrist = landmarks[0]
    thumb_tip = landmarks[4]
    thumb_joint = landmarks[2]

    tip_distance = distance_between_points(thumb_tip, wrist)
    joint_distance = distance_between_points(thumb_joint, wrist)

    return tip_distance > joint_distance * 1.25


def detect_hang_loose(landmarks) -> bool:
    """
    Strict shaka / hang-loose detection.

    Requirements:
    - Thumb and pinky clearly extended
    - Index, middle, and ring clearly folded
    - Thumb and pinky separated widely
    - Gesture must not also look like pointing
    """

    # Prevent pointing from being classified as hang loose.
    if detect_point_direction(landmarks) != PointDirection.NONE:
        return False

    wrist = landmarks[0]
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    index_mcp = landmarks[5]
    middle_mcp = landmarks[9]
    ring_mcp = landmarks[13]
    pinky_mcp = landmarks[17]

    thumb_distance = distance_between_points(thumb_tip, wrist)
    pinky_distance = distance_between_points(pinky_tip, wrist)

    index_distance = distance_between_points(index_tip, wrist)
    middle_distance = distance_between_points(middle_tip, wrist)
    ring_distance = distance_between_points(ring_tip, wrist)

    palm_width = distance_between_points(index_mcp, pinky_mcp)

    thumb_extended = thumb_distance > palm_width * 1.35
    pinky_extended = pinky_distance > palm_width * 1.55

    index_folded = index_distance < palm_width * 1.45
    middle_folded = middle_distance < palm_width * 1.45
    ring_folded = ring_distance < palm_width * 1.45

    thumb_pinky_spread = (
        distance_between_points(thumb_tip, pinky_tip)
        > palm_width * 2.1
    )

    # Shaka is usually wider horizontally than vertically.
    horizontal_span = abs(thumb_tip.x - pinky_tip.x)
    vertical_span = abs(thumb_tip.y - pinky_tip.y)

    mostly_horizontal = horizontal_span > vertical_span * 1.2

    return (
        thumb_extended
        and pinky_extended
        and index_folded
        and middle_folded
        and ring_folded
        and thumb_pinky_spread
        and mostly_horizontal
    )


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

    for landmarks in detected_hands:
        if detect_hang_loose(landmarks):
            return GlobalGesture.HANG_LOOSE

    if (
        len(detected_hands) >= 2
        and detect_prayer_hands(
            detected_hands[0],
            detected_hands[1],
        )
    ):
        return GlobalGesture.PRAYER

    return GlobalGesture.NONE