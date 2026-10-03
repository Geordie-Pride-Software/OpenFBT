import os
import cv2

from src.input.Camera.Camera import Camera
from src.input.Camera.Frame import Frame
from src.tracking.PoseEstimation.PoseEstimator import PoseEstimator


MODEL_PATH = "models/pose_landmarker_full.task"


def main():
    if not os.path.exists(MODEL_PATH):
        print("ERROR: Pose model not found.")
        print(f"Expected: {MODEL_PATH}")
        return

    camera = Camera()

    if not camera.open():
        print("ERROR: Could not connect to camera.")
        return

    estimator = PoseEstimator(MODEL_PATH)

    print("Pose estimator started.")
    print("Press Q to quit.")

    try:
        while True:
            frame_data = camera.read()

            if frame_data is None:
                print("ERROR: Could not read frame.")
                break

            frame = Frame(
                frame_data,
                camera.width,
                camera.height
            )

            pose = estimator.estimate(frame)

            display = frame.get_data()

            if pose is None:
                cv2.putText(
                    display,
                    "No person detected",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )
            else:
                landmarks = pose.get_landmarks()

                cv2.putText(
                    display,
                    f"Landmarks: {len(landmarks)}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

                for landmark in landmarks.values():
                    x = int(
                        landmark.get_image_x()
                        * frame.get_width()
                    )

                    y = int(
                        landmark.get_image_y()
                        * frame.get_height()
                    )

                    cv2.circle(
                        display,
                        (x, y),
                        4,
                        (0, 255, 0),
                        -1
                    )

            cv2.imshow(
                "OpenFBT Pose Estimator Test",
                display
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        estimator.close()
        camera.close()
        cv2.destroyAllWindows()

    print("Pose estimator test finished.")


if __name__ == "__main__":
    main()