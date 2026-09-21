import asyncio
import time

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision

from devices.kasa_controller import KasaController
from vision.gestures import (
    GlobalGesture,
    HandCommand,
    PointDirection,
    detect_global_gesture,
    detect_hand_command,
    detect_point_direction,
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MODEL_PATH = "hand_landmarker.task"

DESK_LAMP_IP = "192.168.4.21"
CABINET_LAMP_IP = "192.168.4.27"

CAMERA_INDEX = 0
MIRROR_CAMERA = True

STABLE_FRAME_REQUIREMENT = 8
NEUTRAL_FRAME_REQUIREMENT = 8
GLOBAL_STABLE_FRAME_REQUIREMENT = 15
DIRECTIONAL_STABLE_FRAME_REQUIREMENT = 8


# --------------------------------------------------
# Drawing
# --------------------------------------------------

def draw_hand(frame, landmarks, label: str) -> None:
    height, width, _ = frame.shape

    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (17, 18), (18, 19), (19, 20),
        (0, 17),
    ]

    points = [
        (
            int(landmark.x * width),
            int(landmark.y * height),
        )
        for landmark in landmarks
    ]

    for start_index, end_index in connections:
        cv2.line(
            frame,
            points[start_index],
            points[end_index],
            (255, 255, 255),
            2,
        )

    for point in points:
        cv2.circle(
            frame,
            point,
            4,
            (0, 255, 0),
            -1,
        )

    wrist_x, wrist_y = points[0]

    cv2.putText(
        frame,
        label,
        (wrist_x, max(30, wrist_y - 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
    )


# --------------------------------------------------
# Dynamic hand roles
# --------------------------------------------------

def detect_hand_roles(detected_hands):
    point_direction = PointDirection.NONE
    hand_command = HandCommand.NONE

    pointing_hand_index = None
    command_hand_index = None

    for index, landmarks in enumerate(detected_hands):
        detected_point = detect_point_direction(landmarks)

        if detected_point != PointDirection.NONE:
            point_direction = detected_point
            pointing_hand_index = index
            break

    if pointing_hand_index is not None:
        for index, landmarks in enumerate(detected_hands):
            if index == pointing_hand_index:
                continue

            detected_command = detect_hand_command(landmarks)

            if detected_command != HandCommand.NONE:
                hand_command = detected_command
                command_hand_index = index
                break

    return (
        point_direction,
        hand_command,
        pointing_hand_index,
        command_hand_index,
    )


# --------------------------------------------------
# Lamp commands
# --------------------------------------------------

async def execute_directional_command(
    direction: PointDirection,
    hand_command: HandCommand,
    desk_lamp: KasaController,
    cabinet_lamp: KasaController,
) -> str:
    if direction == PointDirection.LEFT:
        selected_lamp = desk_lamp
        selected_name = "DESK LAMP"

    elif direction == PointDirection.RIGHT:
        selected_lamp = cabinet_lamp
        selected_name = "CABINET LAMP"

    else:
        return "READY"

    if hand_command == HandCommand.OPEN:
        await selected_lamp.turn_on()
        return f"{selected_name} ON"

    if hand_command == HandCommand.FIST:
        await selected_lamp.turn_off()
        return f"{selected_name} OFF"

    return "READY"


async def execute_global_command(
    global_gesture: GlobalGesture,
    desk_lamp: KasaController,
    cabinet_lamp: KasaController,
) -> str:
    if global_gesture == GlobalGesture.PRAYER:
        # Send both commands concurrently.
        await asyncio.gather(
            desk_lamp.turn_on(),
            cabinet_lamp.turn_on(),
        )
        return "BOTH LAMPS ON"

    if global_gesture == GlobalGesture.HANG_LOOSE:
        await asyncio.gather(
            desk_lamp.turn_off(),
            cabinet_lamp.turn_off(),
        )
        return "BOTH LAMPS OFF"

    return "READY"


# --------------------------------------------------
# Camera loop
# --------------------------------------------------

async def run_camera(
    desk_lamp: KasaController,
    cabinet_lamp: KasaController,
) -> None:
    options = vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=MODEL_PATH
        ),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        raise RuntimeError(
            f"Could not open camera index {CAMERA_INDEX}"
        )

    current_candidate = None
    candidate_frames = 0
    neutral_frames = 0
    armed = True

    status_message = "READY"
    last_timestamp_ms = 0

    try:
        with vision.HandLandmarker.create_from_options(options) as landmarker:
            while True:
                success, frame = camera.read()

                if not success:
                    print("Could not read a frame from the camera.")
                    break

                if MIRROR_CAMERA:
                    frame = cv2.flip(frame, 1)

                rgb_frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB,
                )

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame,
                )

                timestamp_ms = time.monotonic_ns() // 1_000_000

                if timestamp_ms <= last_timestamp_ms:
                    timestamp_ms = last_timestamp_ms + 1

                last_timestamp_ms = timestamp_ms

                result = landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )

                detected_hands = result.hand_landmarks

                # Global gestures receive priority.
                global_gesture = detect_global_gesture(
                    detected_hands
                )

                (
                    point_direction,
                    hand_command,
                    pointing_hand_index,
                    command_hand_index,
                ) = detect_hand_roles(detected_hands)

                # A global gesture overrides hand roles.
                if global_gesture != GlobalGesture.NONE:
                    point_direction = PointDirection.NONE
                    hand_command = HandCommand.NONE
                    pointing_hand_index = None
                    command_hand_index = None

                for index, landmarks in enumerate(detected_hands):
                    if global_gesture == GlobalGesture.PRAYER:
                        role_label = "PRAYER"

                    elif global_gesture == GlobalGesture.HANG_LOOSE:
                        role_label = "HANG LOOSE"

                    elif index == pointing_hand_index:
                        role_label = "POINTING HAND"

                    elif index == command_hand_index:
                        role_label = "COMMAND HAND"

                    else:
                        role_label = "HAND"

                    draw_hand(
                        frame,
                        landmarks,
                        role_label,
                    )

                if global_gesture != GlobalGesture.NONE:
                    candidate = (
                        "global",
                        global_gesture,
                    )
                    valid_combination = True

                elif (
                    point_direction != PointDirection.NONE
                    and hand_command != HandCommand.NONE
                ):
                    candidate = (
                        "directional",
                        point_direction,
                        hand_command,
                    )
                    valid_combination = True

                else:
                    candidate = None
                    valid_combination = False

                # ----------------------------------------
                # Stability and debounce
                # ----------------------------------------

                if not valid_combination:
                    current_candidate = None
                    candidate_frames = 0
                    neutral_frames += 1

                    if neutral_frames >= NEUTRAL_FRAME_REQUIREMENT:
                        armed = True
                        status_message = "READY"

                else:
                    neutral_frames = 0

                    if candidate == current_candidate:
                        candidate_frames += 1
                    else:
                        current_candidate = candidate
                        candidate_frames = 1

                    required_frames = (
                        GLOBAL_STABLE_FRAME_REQUIREMENT
                        if global_gesture != GlobalGesture.NONE
                        else DIRECTIONAL_STABLE_FRAME_REQUIREMENT
                    )

                    if armed and candidate_frames >= required_frames:
                        if global_gesture != GlobalGesture.NONE:
                            status_message = await execute_global_command(
                                global_gesture=global_gesture,
                                desk_lamp=desk_lamp,
                                cabinet_lamp=cabinet_lamp,
                            )

                        else:
                            status_message = (
                                await execute_directional_command(
                                    direction=point_direction,
                                    hand_command=hand_command,
                                    desk_lamp=desk_lamp,
                                    cabinet_lamp=cabinet_lamp,
                                )
                            )

                        print(status_message)

                        armed = False
                        candidate_frames = 0

                # ----------------------------------------
                # Display
                # ----------------------------------------

                cv2.putText(
                    frame,
                    f"Global: {global_gesture.value.upper()}",
                    (25, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Pointing: {point_direction.value.upper()}",
                    (25, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Command: {hand_command.value.upper()}",
                    (25, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Status: {status_message}",
                    (25, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                if not armed:
                    cv2.putText(
                        frame,
                        "Relax hands to reset",
                        (25, 175),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 165, 255),
                        2,
                    )

                cv2.imshow(
                    "Gesture Home Automation",
                    frame,
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                await asyncio.sleep(0)

    finally:
        camera.release()
        cv2.destroyAllWindows()


# --------------------------------------------------
# Program entry point
# --------------------------------------------------

async def main() -> None:
    desk_lamp = KasaController(DESK_LAMP_IP)
    cabinet_lamp = KasaController(CABINET_LAMP_IP)

    try:
        print("Connecting to Desk Lamp...")
        await desk_lamp.connect()

        print("Connecting to Cabinet Lamp...")
        await cabinet_lamp.connect()

        print()
        print("Controls:")
        print("Prayer hands                  = both lamps ON")
        print("Hang loose with either hand   = both lamps OFF")
        print("Point left + other hand open  = Desk Lamp ON")
        print("Point left + other hand fist  = Desk Lamp OFF")
        print("Point right + other hand open = Cabinet Lamp ON")
        print("Point right + other hand fist = Cabinet Lamp OFF")
        print()
        print("Press Q in the camera window to quit.")

        await run_camera(
            desk_lamp=desk_lamp,
            cabinet_lamp=cabinet_lamp,
        )

    finally:
        await desk_lamp.disconnect()
        await cabinet_lamp.disconnect()
        print("Disconnected from both lamps.")


if __name__ == "__main__":
    asyncio.run(main())