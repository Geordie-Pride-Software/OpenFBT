#include "Protocol.hpp"

#include <cmath>
#include <cstring>

namespace
{
    float readFloat(const std::uint8_t* data)
    {
        // The Python side sends little endian, and so do all machines that
        // run SteamVR, so a plain copy is enough.
        float value;
        std::memcpy(&value, data, sizeof(float));
        return value;
    }
}

bool Protocol::parse(const std::uint8_t* data, std::size_t size, TrackerPacket& out)
{
    if (size != PACKET_SIZE)
        return false;

    if (std::memcmp(data, "OFBT", 4) != 0)
        return false;

    if (data[4] != VERSION)
        return false;

    int id = data[5];

    if (id >= TRACKER_COUNT)
        return false;

    double values[7];

    for (int i = 0; i < 7; i++)
    {
        float value = readFloat(data + 8 + i * 4);

        if (!std::isfinite(value))
            return false;

        values[i] = value;
    }

    double length = std::sqrt(
        values[3] * values[3] +
        values[4] * values[4] +
        values[5] * values[5] +
        values[6] * values[6]
    );

    if (length < 1e-6)
        return false;

    out.id = id;
    out.valid = (data[6] & 1) != 0;

    for (int i = 0; i < 3; i++)
        out.position[i] = values[i];

    for (int i = 0; i < 4; i++)
        out.rotation[i] = values[3 + i] / length;

    return true;
}
