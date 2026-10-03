import socket
import struct


class SteamVrOutput:
    """
    Sends trackers to the OpenFBT SteamVR driver over UDP on localhost.

    Packet layout (little endian, 36 bytes), see Driver/Protocol.hpp:
        4s magic "OFBT", B version, B tracker id, B flags, B reserved,
        3f position (metres), 4f rotation (x, y, z, w)

    The solver already uses OpenVR's axes (X right, Y up, Z back), so
    nothing is converted here.
    """

    MAGIC = b"OFBT"
    VERSION = 1
    FORMAT = "<4sBBBB3f4f"

    IDS = {
        "hips": 0,
        "chest": 1,
        "left_foot": 2,
        "right_foot": 3,
        "left_knee": 4,
        "right_knee": 5,
        "left_elbow": 6,
        "right_elbow": 7,
    }

    def __init__(self, host="127.0.0.1", port=43210):
        self.address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @classmethod
    def encode(cls, tracker_id, position, rotation, valid=True):
        return struct.pack(
            cls.FORMAT,
            cls.MAGIC,
            cls.VERSION,
            tracker_id,
            1 if valid else 0,
            0,
            float(position[0]), float(position[1]), float(position[2]),
            float(rotation[0]), float(rotation[1]),
            float(rotation[2]), float(rotation[3])
        )

    def send(self, trackers):
        for name, tracker in trackers.items():
            tracker_id = self.IDS.get(name)

            if tracker_id is None:
                continue

            self.socket.sendto(
                self.encode(tracker_id, tracker.position, tracker.rotation),
                self.address
            )

    def close(self):
        self.socket.close()
