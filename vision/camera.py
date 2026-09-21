import cv2

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None


class OpenCvCamera:
    """Wraps a USB webcam via OpenCV, used on the PC prototype."""

    def __init__(self, index: int) -> None:
        self.capture = cv2.VideoCapture(index)

        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open camera index {index}")

    def read(self):
        return self.capture.read()

    def release(self) -> None:
        self.capture.release()


class PiCsiCamera:
    """Wraps the Raspberry Pi CSI camera via Picamera2."""

    def __init__(self, size: tuple[int, int] = (1280, 720)) -> None:
        self.picam2 = Picamera2()

        # Despite the name, Picamera2's "RGB888" format stores pixels in
        # BGR order in memory, matching what OpenCV/cv2 expects here.
        config = self.picam2.create_video_configuration(
            main={"size": size, "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

    def read(self):
        frame = self.picam2.capture_array("main")
        return True, frame

    def release(self) -> None:
        self.picam2.stop()


def open_camera(index: int):
    if Picamera2 is not None:
        return PiCsiCamera()

    return OpenCvCamera(index)
