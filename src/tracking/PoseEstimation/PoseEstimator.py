import time

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .Pose import Pose, Landmark


class PoseEstimator:
    LANDMARK_NAMES = [
        "nose",

        "left_eye_inner",
        "left_eye",
        "left_eye_outer",

        "right_eye_inner",
        "right_eye",
        "right_eye_outer",

        "left_ear",
        "right_ear",

        "mouth_left",
        "mouth_right",

        "left_shoulder",
        "right_shoulder",

        "left_elbow",
        "right_elbow",

        "left_wrist",
        "right_wrist",

        "left_pinky",
        "right_pinky",

        "left_index",
        "right_index",

        "left_thumb",
        "right_thumb",

        "left_hip",
        "right_hip",

        "left_knee",
        "right_knee",

        "left_ankle",
        "right_ankle",

        "left_heel",
        "right_heel",

        "left_foot_index",
        "right_foot_index"
    ]

    def __init__(
        self,
        model_path,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    ):
        self.model_path = model_path

        self.min_pose_detection_confidence = (
            min_pose_detection_confidence
        )

        self.min_pose_presence_confidence = (
            min_pose_presence_confidence
        )

        self.min_tracking_confidence = (
            min_tracking_confidence
        )

        self.landmarker = None
        self._last_timestamp_ms = -1

        self._load_model()

    def _load_model(self):
        base_options = python.BaseOptions(
            model_asset_path=self.model_path
        )

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=(
                self.min_pose_detection_confidence
            ),
            min_pose_presence_confidence=(
                self.min_pose_presence_confidence
            ),
            min_tracking_confidence=(
                self.min_tracking_confidence
            )
        )

        self.landmarker = vision.PoseLandmarker.create_from_options(
            options
        )

    def estimate(self, frame, timestamp_ms=None):
        if self.landmarker is None:
            raise RuntimeError(
                "PoseEstimator has not been initialized."
            )

        if frame is None:
            return None

        image_data = frame.get_data()

        if image_data is None:
            return None

        # OpenCV frames are BGR, MediaPipe expects RGB.
        rgb = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        # VIDEO mode needs timestamps that always increase.
        if timestamp_ms is None:
            timestamp_ms = int(time.monotonic() * 1000)

        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1

        self._last_timestamp_ms = timestamp_ms

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        if not result.pose_landmarks:
            return None

        image_landmarks = result.pose_landmarks[0]

        world_landmarks = None

        if result.pose_world_landmarks:
            world_landmarks = result.pose_world_landmarks[0]

        landmarks = {}

        for index, image_landmark in enumerate(image_landmarks):
            name = self.LANDMARK_NAMES[index]

            if world_landmarks is not None:
                world_landmark = world_landmarks[index]

                world_x = world_landmark.x
                world_y = world_landmark.y
                world_z = world_landmark.z
            else:
                world_x = 0.0
                world_y = 0.0
                world_z = 0.0

            landmarks[name] = Landmark(
                name=name,
                image_x=image_landmark.x,
                image_y=image_landmark.y,
                world_x=world_x,
                world_y=world_y,
                world_z=world_z,
                visibility=getattr(
                    image_landmark,
                    "visibility",
                    1.0
                ),
                presence=getattr(
                    image_landmark,
                    "presence",
                    1.0
                )
            )

        return Pose(landmarks)

    def close(self):
        if self.landmarker is not None:
            self.landmarker.close()
            self.landmarker = None