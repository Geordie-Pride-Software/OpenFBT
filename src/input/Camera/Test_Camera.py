import cv2

from Camera import Camera


def main():
    camera = Camera()

    if not camera.open():
        print("ERROR: Failed to open camera.")
        return

    print("Camera connected successfully.")
    print("Press Q to close the camera.")

    while camera.is_open():
        frame = camera.read()

        if frame is None:
            print("ERROR: Failed to read frame.")
            break

        cv2.imshow("OpenFBT Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.close()
    cv2.destroyAllWindows()

    print("Camera closed.")


if __name__ == "__main__":
    main()