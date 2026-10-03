import socket
import struct

from src.tracking.Solver.MathUtil import (
    to_unity_euler_degrees,
    to_unity_position,
)


def _pad(data):
    # OSC strings end with at least one null and are padded to 4 bytes.
    return data + b"\x00" * (4 - len(data) % 4)


def encode_message(address, *floats):
    tags = "," + "f" * len(floats)

    return (
        _pad(address.encode("ascii"))
        + _pad(tags.encode("ascii"))
        + struct.pack(">" + "f" * len(floats), *floats)
    )


class OscOutput:
    """
    Sends trackers to VRChat's OSC tracker addresses
    (/tracking/trackers/<1-8>/position and /rotation).

    VRChat matches trackers to body parts itself when you press
    Calibrate in its tracking settings, so the slot order only needs
    to stay the same from run to run.
    """

    SLOTS = {
        "hips": 1,
        "left_foot": 2,
        "right_foot": 3,
        "chest": 4,
        "left_knee": 5,
        "right_knee": 6,
        "left_elbow": 7,
        "right_elbow": 8,
    }

    def __init__(self, host="127.0.0.1", port=9000):
        self.address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, trackers):
        for name, tracker in trackers.items():
            slot = self.SLOTS.get(name)

            if slot is None:
                continue

            position = to_unity_position(tracker.position)
            rotation = to_unity_euler_degrees(tracker.rotation)

            self.socket.sendto(
                encode_message(
                    f"/tracking/trackers/{slot}/position",
                    *[float(c) for c in position]
                ),
                self.address
            )

            self.socket.sendto(
                encode_message(
                    f"/tracking/trackers/{slot}/rotation",
                    *[float(c) for c in rotation]
                ),
                self.address
            )

    def close(self):
        self.socket.close()
