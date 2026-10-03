from dataclasses import dataclass

import numpy as np

from .MathUtil import (
    basis_rotation,
    look_rotation,
    normalize,
    remove_component,
)
from .OneEuroFilter import OneEuroFilter, QuaternionFilter


WORLD_UP = np.array([0.0, 1.0, 0.0])

TRACKER_NAMES = [
    "hips",
    "chest",
    "left_foot",
    "right_foot",
    "left_knee",
    "right_knee",
    "left_elbow",
    "right_elbow",
]


@dataclass
class TrackerPose:
    name: str
    position: np.ndarray
    rotation: np.ndarray
    confidence: float


class TrackerSolver:
    """
    Turns a Pose (MediaPipe landmarks) into smoothed body trackers.

    Output frame: right-handed, X right, Y up, Z towards the back of the
    person, metres, floor at Y = 0 after calibration.
    """

    def __init__(
        self,
        min_visibility=0.5,
        track_translation=True,
        aspect_ratio=16.0 / 9.0,
        position_cutoff=1.5,
        position_beta=0.3,
        rotation_cutoff=1.5,
        rotation_beta=0.2
    ):
        self.min_visibility = min_visibility
        self.track_translation = track_translation
        self.aspect_ratio = aspect_ratio

        self.floor_y = None
        self._calibration_samples = []

        self._position_filters = {
            name: OneEuroFilter(position_cutoff, position_beta)
            for name in TRACKER_NAMES
        }
        self._rotation_filters = {
            name: QuaternionFilter(rotation_cutoff, rotation_beta)
            for name in TRACKER_NAMES
        }

        self._last = {}

    # Calibration

    def start_calibration(self):
        """Stand still and upright, then call finish_calibration()."""
        self._calibration_samples = []
        self.floor_y = None

    def add_calibration_sample(self, pose):
        if pose is None:
            return False

        lowest = self._lowest_foot_y(pose)

        if lowest is None:
            return False

        self._calibration_samples.append(lowest)
        return True

    def finish_calibration(self):
        if not self._calibration_samples:
            return False

        self.floor_y = float(np.median(self._calibration_samples))
        self._calibration_samples = []
        return True

    def is_calibrated(self):
        return self.floor_y is not None

    # Solving

    def solve(self, pose, t):
        """
        Returns a dict of tracker name -> TrackerPose.
        If there is no pose, returns the last known trackers.
        """
        if pose is None:
            return dict(self._last)

        pts = self._world_points(pose)
        vis = self._visibilities(pose)

        floor_y = self.floor_y

        if floor_y is None:
            floor_y = self._lowest_foot_y(pose)

        offset = np.array([0.0, -floor_y, 0.0]) if floor_y is not None else np.zeros(3)

        if self.track_translation:
            offset = offset + self._translation(pose, pts)

        raw = self._raw_trackers(pts, vis)

        result = dict(self._last)

        for name, (position, rotation, confidence) in raw.items():
            if confidence < self.min_visibility:
                continue

            if position is None or rotation is None:
                continue

            smooth_position = self._position_filters[name](position + offset, t)
            smooth_rotation = self._rotation_filters[name](rotation, t)

            result[name] = TrackerPose(
                name,
                smooth_position,
                smooth_rotation,
                confidence
            )

        self._last = result

        return dict(result)

    # Internals

    @staticmethod
    def _to_solver_frame(landmark):
        # MediaPipe world: X image right, Y down, Z away from the camera.
        # Solver frame: X person's right, Y up, Z person's back.
        return np.array([
            -landmark.get_world_x(),
            -landmark.get_world_y(),
            landmark.get_world_z()
        ])

    def _world_points(self, pose):
        return {
            name: self._to_solver_frame(landmark)
            for name, landmark in pose.get_landmarks().items()
        }

    @staticmethod
    def _visibilities(pose):
        return {
            name: landmark.get_visibility()
            for name, landmark in pose.get_landmarks().items()
        }

    def _lowest_foot_y(self, pose):
        names = [
            "left_heel", "right_heel",
            "left_foot_index", "right_foot_index",
            "left_ankle", "right_ankle"
        ]

        ys = [
            self._to_solver_frame(pose.get_landmark(n))[1]
            for n in names
            if pose.has_landmark(n)
            and pose.get_landmark(n).get_visibility() >= self.min_visibility
        ]

        if not ys:
            return None

        return min(ys)

    def _translation(self, pose, pts):
        """
        MediaPipe world landmarks are centred on the hips, so walking
        around the room is lost. Recover sideways movement from where
        the hips sit in the image, scaled by the torso size.
        """
        needed = ["left_hip", "right_hip", "left_shoulder", "right_shoulder"]

        if not all(pose.has_landmark(n) for n in needed):
            return np.zeros(3)

        lh = pose.get_landmark("left_hip")
        rh = pose.get_landmark("right_hip")
        ls = pose.get_landmark("left_shoulder")
        rs = pose.get_landmark("right_shoulder")

        hip_x = (lh.get_image_x() + rh.get_image_x()) / 2.0
        hip_y = (lh.get_image_y() + rh.get_image_y()) / 2.0
        sho_x = (ls.get_image_x() + rs.get_image_x()) / 2.0
        sho_y = (ls.get_image_y() + rs.get_image_y()) / 2.0

        # Torso length in image-height units.
        dx = (sho_x - hip_x) * self.aspect_ratio
        dy = sho_y - hip_y
        torso_image = float(np.hypot(dx, dy))

        torso_world = np.linalg.norm(
            (pts["left_shoulder"] + pts["right_shoulder"]) / 2.0
            - (pts["left_hip"] + pts["right_hip"]) / 2.0
        )

        if torso_image < 1e-4 or torso_world < 1e-4:
            return np.zeros(3)

        metres_per_unit = torso_world / torso_image

        # Image X grows to the image right, which is the person's left.
        sideways = -(hip_x - 0.5) * self.aspect_ratio * metres_per_unit

        return np.array([sideways, 0.0, 0.0])

    def _raw_trackers(self, pts, vis):
        def v(*names):
            return min(vis.get(n, 0.0) for n in names)

        def have(*names):
            return all(n in pts for n in names)

        out = {}

        hip_mid = None
        shoulder_mid = None
        body_up = WORLD_UP
        chest_forward = None

        if have("left_hip", "right_hip"):
            hip_mid = (pts["left_hip"] + pts["right_hip"]) / 2.0

        if have("left_shoulder", "right_shoulder"):
            shoulder_mid = (pts["left_shoulder"] + pts["right_shoulder"]) / 2.0

        if hip_mid is not None and shoulder_mid is not None:
            spine = normalize(shoulder_mid - hip_mid)

            if spine is not None:
                body_up = spine

        # Hips
        if hip_mid is not None:
            right = pts["right_hip"] - pts["left_hip"]
            rotation = basis_rotation(right, body_up)

            out["hips"] = (
                hip_mid,
                rotation,
                v("left_hip", "right_hip")
            )

        # Chest
        if hip_mid is not None and shoulder_mid is not None:
            right = pts["right_shoulder"] - pts["left_shoulder"]
            rotation = basis_rotation(right, body_up)
            position = hip_mid + (shoulder_mid - hip_mid) * 0.7

            out["chest"] = (
                position,
                rotation,
                v("left_hip", "right_hip", "left_shoulder", "right_shoulder")
            )

            if rotation is not None:
                chest_forward = -np.array([
                    2 * (rotation[0] * rotation[2] + rotation[1] * rotation[3]),
                    2 * (rotation[1] * rotation[2] - rotation[0] * rotation[3]),
                    1 - 2 * (rotation[0] ** 2 + rotation[1] ** 2)
                ])

        # Legs
        for side in ("left", "right"):
            hip = f"{side}_hip"
            knee = f"{side}_knee"
            ankle = f"{side}_ankle"
            heel = f"{side}_heel"
            toe = f"{side}_foot_index"

            foot_forward = None

            if have(heel, toe):
                foot_forward = pts[toe] - pts[heel]

            if have(ankle, heel, toe):
                rotation = look_rotation(foot_forward, WORLD_UP)

                out[f"{side}_foot"] = (
                    pts[ankle],
                    rotation,
                    v(ankle, heel, toe)
                )

            if have(hip, knee):
                up = pts[hip] - pts[knee]

                forward = foot_forward

                if forward is None:
                    forward = chest_forward

                if forward is None:
                    continue

                forward = remove_component(forward, up)
                rotation = look_rotation(forward, up)

                out[f"{side}_knee"] = (
                    pts[knee],
                    rotation,
                    v(hip, knee)
                )

        # Arms
        for side in ("left", "right"):
            shoulder = f"{side}_shoulder"
            elbow = f"{side}_elbow"

            if not have(shoulder, elbow) or chest_forward is None:
                continue

            up = pts[shoulder] - pts[elbow]
            forward = remove_component(chest_forward, up)
            rotation = look_rotation(forward, up)

            out[f"{side}_elbow"] = (
                pts[elbow],
                rotation,
                v(shoulder, elbow)
            )

        return out
