import math
import os
import struct
import unittest

import numpy as np

from src.Output.OSC.OscOutput import encode_message
from src.tracking.PoseEstimation.Pose import Landmark, Pose
from src.tracking.Solver.MathUtil import (
    quaternion_from_axis_angle,
    to_unity_euler_degrees,
    to_unity_position,
)
from src.tracking.Solver.TrackerSolver import TRACKER_NAMES, TrackerSolver


def standing_pose(shift_x=0.0):
    """
    A person facing the camera, in MediaPipe world coordinates
    (metres, origin at the hips, Y down, Z away from the camera).
    """
    # name: (world_x, world_y, world_z); image-left is negative X,
    # so the person's right side is on the negative X side.
    points = {
        "left_shoulder": (0.20, -0.50, 0.0),
        "right_shoulder": (-0.20, -0.50, 0.0),
        "left_elbow": (0.25, -0.20, 0.0),
        "right_elbow": (-0.25, -0.20, 0.0),
        "left_wrist": (0.27, 0.05, 0.0),
        "right_wrist": (-0.27, 0.05, 0.0),
        "left_hip": (0.10, 0.0, 0.0),
        "right_hip": (-0.10, 0.0, 0.0),
        "left_knee": (0.10, 0.45, 0.0),
        "right_knee": (-0.10, 0.45, 0.0),
        "left_ankle": (0.10, 0.88, 0.0),
        "right_ankle": (-0.10, 0.88, 0.0),
        "left_heel": (0.10, 0.92, 0.03),
        "right_heel": (-0.10, 0.92, 0.03),
        # Toes point towards the camera, which is negative Z.
        "left_foot_index": (0.10, 0.92, -0.15),
        "right_foot_index": (-0.10, 0.92, -0.15),
    }

    landmarks = {}

    for name, (x, y, z) in points.items():
        landmarks[name] = Landmark(
            name,
            0.5 + shift_x - x * 0.5,
            0.5 + y * 0.4,
            x,
            y,
            z,
            visibility=0.99
        )

    return Pose(landmarks)


def rotate(q, v):
    from src.tracking.Solver.MathUtil import rotate_vector
    return rotate_vector(q, v)


class OscTests(unittest.TestCase):
    def test_message_layout(self):
        data = encode_message("/tracking/trackers/1/position", 1.0, 2.0, 3.0)

        self.assertEqual(len(data) % 4, 0)
        self.assertTrue(data.startswith(b"/tracking/trackers/1/position\x00"))
        self.assertIn(b",fff\x00", data)
        self.assertEqual(struct.unpack(">fff", data[-12:]), (1.0, 2.0, 3.0))

    def test_padding_when_length_is_multiple_of_four(self):
        data = encode_message("/abc", 0.0)
        # "/abc" is 4 bytes and still needs a null terminator, padded to 8.
        self.assertTrue(data.startswith(b"/abc\x00\x00\x00\x00"))


class SteamVrPacketTests(unittest.TestCase):
    def test_packet_layout(self):
        from src.Output.SteamVR.SteamVrOutput import SteamVrOutput

        data = SteamVrOutput.encode(
            3, [1.0, 2.0, 3.0], [0.0, 0.0, 0.0, 1.0], valid=True
        )

        self.assertEqual(len(data), 36)
        self.assertEqual(data[:4], b"OFBT")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 3)
        self.assertEqual(data[6], 1)
        self.assertEqual(struct.unpack("<3f", data[8:20]), (1.0, 2.0, 3.0))
        self.assertEqual(struct.unpack("<4f", data[20:36]), (0.0, 0.0, 0.0, 1.0))

    def test_every_tracker_has_an_id(self):
        from src.Output.SteamVR.SteamVrOutput import SteamVrOutput

        self.assertEqual(sorted(SteamVrOutput.IDS), sorted(TRACKER_NAMES))
        self.assertEqual(sorted(SteamVrOutput.IDS.values()), list(range(8)))


class MathTests(unittest.TestCase):
    def test_identity_is_zero_euler(self):
        e = to_unity_euler_degrees(np.array([0.0, 0.0, 0.0, 1.0]))
        self.assertTrue(np.allclose(e % 360.0, [0.0, 0.0, 0.0], atol=1e-6))

    def test_position_flips_z(self):
        self.assertTrue(np.allclose(
            to_unity_position([1.0, 2.0, 3.0]), [1.0, 2.0, -3.0]
        ))

    def test_yaw_matches_unity(self):
        # Turning left by 90 degrees (anticlockwise seen from above) in the
        # right-handed frame is a -90 degree yaw in Unity (turning left).
        q = quaternion_from_axis_angle([0, 1, 0], 90.0)
        e = to_unity_euler_degrees(q)
        self.assertAlmostEqual(e[1], 270.0, places=3)
        self.assertAlmostEqual(e[0] % 360.0, 0.0, places=3)


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.solver = TrackerSolver(aspect_ratio=1.0)
        self.trackers = self.solver.solve(standing_pose(), 0.0)

    def test_all_trackers_present(self):
        self.assertEqual(sorted(self.trackers), sorted(TRACKER_NAMES))

    def test_feet_sit_near_the_floor_and_hips_above(self):
        left = self.trackers["left_foot"].position
        hips = self.trackers["hips"].position

        # Ankle is 4 cm above the heel, which is the lowest point.
        self.assertAlmostEqual(left[1], 0.04, places=2)
        self.assertGreater(hips[1], 0.8)

    def test_right_is_positive_x_for_the_person(self):
        self.assertGreater(
            self.trackers["right_foot"].position[0],
            self.trackers["left_foot"].position[0]
        )

    def test_hips_and_feet_face_the_camera(self):
        # Forward is -Z. The person faces the camera, so the tracker
        # forward vector should point to -Z in the solver frame, and
        # tracker local -Z is the forward axis.
        for name in ("hips", "chest", "left_foot", "right_foot"):
            forward = rotate(self.trackers[name].rotation, [0, 0, -1])
            self.assertLess(forward[2], -0.9, name)

    def test_calibration_sets_floor(self):
        solver = TrackerSolver(aspect_ratio=1.0)
        solver.start_calibration()

        for _ in range(10):
            self.assertTrue(solver.add_calibration_sample(standing_pose()))

        self.assertTrue(solver.finish_calibration())
        self.assertTrue(solver.is_calibrated())

        trackers = solver.solve(standing_pose(), 0.0)
        self.assertAlmostEqual(trackers["left_foot"].position[1], 0.04, places=2)

    def test_low_visibility_holds_last_value(self):
        pose = standing_pose()
        before = self.trackers["left_knee"].position.copy()

        pose.get_landmark("left_knee").visibility = 0.1
        pose.get_landmark("left_knee").world_x += 1.0

        after = self.solver.solve(pose, 0.033)["left_knee"].position

        self.assertTrue(np.allclose(before, after))

    def test_no_pose_returns_last_trackers(self):
        again = self.solver.solve(None, 0.1)
        self.assertEqual(sorted(again), sorted(TRACKER_NAMES))

    def test_moving_in_image_moves_trackers_sideways(self):
        a = TrackerSolver(aspect_ratio=1.0).solve(standing_pose(0.0), 0.0)
        b = TrackerSolver(aspect_ratio=1.0).solve(standing_pose(0.1), 0.0)

        dx = b["hips"].position[0] - a["hips"].position[0]

        # Person moved towards image right, which is their left (negative X).
        self.assertLess(dx, -0.05)


class EstimatorTests(unittest.TestCase):
    MODEL = "models/pose_landmarker_full.task"

    @unittest.skipUnless(os.path.exists(MODEL), "model file missing")
    def test_blank_frame_gives_no_pose(self):
        from src.input.Camera.Frame import Frame
        from src.tracking.PoseEstimation.PoseEstimator import PoseEstimator

        estimator = PoseEstimator(self.MODEL)

        try:
            data = np.zeros((480, 640, 3), dtype=np.uint8)
            frame = Frame(data, 640, 480)

            self.assertIsNone(estimator.estimate(frame, 0))
            self.assertIsNone(estimator.estimate(frame, 33))
            # Same timestamp twice must not crash VIDEO mode.
            self.assertIsNone(estimator.estimate(frame, 33))
        finally:
            estimator.close()


if __name__ == "__main__":
    unittest.main()
