import argparse
import os
import time

import cv2

from src.input.Camera.Camera import Camera
from src.input.Camera.Frame import Frame
from src.Output.OSC.OscOutput import OscOutput
from src.Output.SteamVR.SteamVrOutput import SteamVrOutput
from src.tracking.PoseEstimation.PoseEstimator import PoseEstimator
from src.tracking.Solver.TrackerSolver import TrackerSolver


DEFAULT_MODEL = "models/pose_landmarker_full.task"

CALIBRATION_SECONDS = 2.0

# Pairs of landmarks to draw as the skeleton in the preview window.
BONES = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("left_ankle", "left_heel"),
    ("left_heel", "left_foot_index"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
    ("right_ankle", "right_heel"),
    ("right_heel", "right_foot_index"),
]


def parse_args():
    parser = argparse.ArgumentParser(description="OpenFBT")

    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--output",
        choices=["steamvr", "osc", "both"],
        default="steamvr",
        help="steamvr = OpenFBT SteamVR driver, osc = VRChat OSC trackers."
    )
    parser.add_argument("--osc-host", default="127.0.0.1")
    parser.add_argument("--osc-port", type=int, default=9000)
    parser.add_argument("--steamvr-port", type=int, default=43210)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument(
        "--no-translation",
        action="store_true",
        help="Do not follow sideways movement in the camera image."
    )

    return parser.parse_args()


def draw_preview(frame, pose, trackers, status):
    display = frame.get_data().copy()
    width = frame.get_width()
    height = frame.get_height()

    if pose is not None:
        for a, b in BONES:
            if pose.has_landmark(a) and pose.has_landmark(b):
                la = pose.get_landmark(a)
                lb = pose.get_landmark(b)

                cv2.line(
                    display,
                    (int(la.get_image_x() * width), int(la.get_image_y() * height)),
                    (int(lb.get_image_x() * width), int(lb.get_image_y() * height)),
                    (0, 255, 0),
                    2
                )

    cv2.putText(
        display,
        status,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2
    )

    cv2.putText(
        display,
        f"Trackers: {len(trackers)}   C = calibrate   Q = quit",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    return display


def main():
    args = parse_args()

    if not os.path.exists(args.model):
        print(f"ERROR: Pose model not found: {args.model}")
        return

    camera = Camera(args.camera, args.width, args.height, args.fps)

    if not camera.open():
        print("ERROR: Could not open camera.")
        return

    # The camera may not give exactly the size we asked for.
    actual_width = int(camera.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(camera.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    estimator = PoseEstimator(args.model)

    solver = TrackerSolver(
        track_translation=not args.no_translation,
        aspect_ratio=actual_width / actual_height
    )

    outputs = []

    if args.output in ("steamvr", "both"):
        outputs.append(SteamVrOutput("127.0.0.1", args.steamvr_port))
        print(f"Sending to the SteamVR driver on UDP port {args.steamvr_port}")

    if args.output in ("osc", "both"):
        outputs.append(OscOutput(args.osc_host, args.osc_port))
        print(f"Sending OSC to {args.osc_host}:{args.osc_port}")

    print("Stand upright in view of the camera and press C to calibrate.")

    calibrating_until = None
    status = "Not calibrated"

    if args.no_preview:
        # No window means no key presses, so calibrate automatically.
        solver.start_calibration()
        calibrating_until = time.monotonic() + 3.0 + CALIBRATION_SECONDS
    trackers = {}
    start = time.monotonic()

    try:
        while camera.is_open():
            data = camera.read()

            if data is None:
                print("ERROR: Could not read frame.")
                break

            frame = Frame(data, actual_width, actual_height)
            now = time.monotonic()

            pose = estimator.estimate(frame, int((now - start) * 1000))

            if calibrating_until is not None:
                solver.add_calibration_sample(pose)
                status = "Calibrating, stand still..."

                if now >= calibrating_until:
                    calibrating_until = None

                    if solver.finish_calibration():
                        status = "Calibrated"
                    else:
                        status = "Calibration failed, feet not visible"
            elif solver.is_calibrated():
                status = "Calibrated"

            if pose is None and calibrating_until is None and not trackers:
                status = "No person detected"

            if calibrating_until is None:
                trackers = solver.solve(pose, now - start)

                if trackers:
                    for output in outputs:
                        output.send(trackers)

            if not args.no_preview:
                cv2.imshow(
                    "OpenFBT",
                    draw_preview(frame, pose, trackers, status)
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    break

                if key == ord("c"):
                    solver.start_calibration()
                    calibrating_until = now + CALIBRATION_SECONDS
    finally:
        for output in outputs:
            output.close()
        estimator.close()
        camera.close()
        cv2.destroyAllWindows()

    print("OpenFBT stopped.")


if __name__ == "__main__":
    main()
