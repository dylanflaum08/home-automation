import time

import cv2
import numpy as np


class MotionDetector:
    """
    Cheap frame-difference motion detector, downsampled for speed since it
    only needs to answer "did something move recently", not track anything
    precisely.
    """

    def __init__(self, threshold: int = 25, changed_fraction: float = 0.02) -> None:
        self.threshold = threshold
        self.changed_fraction = changed_fraction
        self._previous_frame = None
        self.last_motion_time: float | None = None

    def update(self, frame_bgr) -> bool:
        small = cv2.resize(frame_bgr, (160, 90))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        motion_detected = False

        if self._previous_frame is not None:
            diff = cv2.absdiff(self._previous_frame, gray)
            changed_pixels = np.count_nonzero(diff > self.threshold)
            fraction = changed_pixels / diff.size

            if fraction > self.changed_fraction:
                motion_detected = True
                self.last_motion_time = time.monotonic()

        self._previous_frame = gray
        return motion_detected

    def motion_since(self, seconds: float) -> bool:
        if self.last_motion_time is None:
            return False

        return (time.monotonic() - self.last_motion_time) < seconds
