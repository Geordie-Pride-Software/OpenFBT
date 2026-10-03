#pragma once

#include <cstddef>
#include <cstdint>

// Packet sent by the Python app to the driver over UDP (little endian, 36 bytes).
//
//   offset  size  field
//   0       4     magic "OFBT"
//   4       1     version (1)
//   5       1     tracker id (0 to 7, see TrackerRoles.hpp)
//   6       1     flags (bit 0 = pose is valid)
//   7       1     reserved
//   8       12    position x, y, z as float32 (metres, X right, Y up, Z back)
//   20      16    rotation x, y, z, w as float32
//
// The axes already match OpenVR, so the driver does not convert anything.

namespace Protocol
{
    const std::size_t PACKET_SIZE = 36;
    const std::uint8_t VERSION = 1;
    const int TRACKER_COUNT = 8;

    struct TrackerPacket
    {
        int id;
        bool valid;
        double position[3];
        double rotation[4]; // x, y, z, w
    };

    // Returns false if the packet is the wrong size, has the wrong magic or
    // version, has a bad tracker id, or contains NaN or infinite numbers.
    bool parse(const std::uint8_t* data, std::size_t size, TrackerPacket& out);
}
