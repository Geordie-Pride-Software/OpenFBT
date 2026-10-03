import cv2


class Camera:
    def __init__(self, camera_id=0, width=1280, height=720, fps=30):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps

        self.capture = None

    def open(self):
        self.capture = cv2.VideoCapture(self.camera_id)

        if not self.capture.isOpened():
            self.capture = None
            return False

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        return True

    def read(self):
        if self.capture is None:
            return None

        success, frame = self.capture.read()

        if not success:
            return None

        return frame

    def is_open(self):
        return self.capture is not None and self.capture.isOpened()

    def close(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None