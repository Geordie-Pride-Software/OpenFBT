#include "ServerDriver.hpp"

#include <string>

#include "TrackerRoles.hpp"

namespace
{
    const char* SETTINGS_SECTION = "driver_openfbt";
    const int DEFAULT_PORT = 43210;

    void log(const std::string& message)
    {
        vr::VRDriverLog()->Log((message + "\n").c_str());
    }
}

vr::EVRInitError ServerDriver::Init(vr::IVRDriverContext* driverContext)
{
    VR_INIT_SERVER_DRIVER_CONTEXT(driverContext);

    vr::EVRSettingsError settingsError = vr::VRSettingsError_None;
    int port = vr::VRSettings()->GetInt32(SETTINGS_SECTION, "port", &settingsError);

    if (settingsError != vr::VRSettingsError_None || port <= 0 || port > 65535)
        port = DEFAULT_PORT;

    for (int id = 0; id < Protocol::TRACKER_COUNT; id++)
    {
        const TrackerRole& role = TRACKER_ROLES[id];

        TrackerDevice* device = new TrackerDevice(id, role.serial, role.controllerType);

        if (!vr::VRServerDriverHost()->TrackedDeviceAdded(
                role.serial,
                vr::TrackedDeviceClass_GenericTracker,
                device))
        {
            log(std::string("OpenFBT: could not add tracker ") + role.serial);
            delete device;
            continue;
        }

        // Tell SteamVR which body part this tracker is.
        std::string key = std::string("/devices/openfbt/") + role.serial;
        vr::VRSettings()->SetString(vr::k_pch_Trackers_Section, key.c_str(), role.steamVrRole);

        devices.push_back(device);
    }

    // Packets are routed to devices by id, and the device list is only
    // changed in Init and Cleanup, so the lookup below is safe.
    std::vector<TrackerDevice*> byId(Protocol::TRACKER_COUNT, nullptr);

    for (TrackerDevice* device : devices)
    {
        for (int id = 0; id < Protocol::TRACKER_COUNT; id++)
        {
            if (device->getSerial() == TRACKER_ROLES[id].serial)
                byId[id] = device;
        }
    }

    bool started = receiver.start(port, [byId](const Protocol::TrackerPacket& packet)
    {
        TrackerDevice* device = byId[packet.id];

        if (device != nullptr)
            device->update(packet);
    });

    if (started)
        log("OpenFBT: listening for trackers on UDP port " + std::to_string(port));
    else
        log("OpenFBT: could not open UDP port " + std::to_string(port));

    return vr::VRInitError_None;
}

void ServerDriver::Cleanup()
{
    // Stop the thread first so nothing touches the devices while they go away.
    receiver.stop();
    devices.clear();
}

const char* const* ServerDriver::GetInterfaceVersions()
{
    return vr::k_InterfaceVersions;
}

void ServerDriver::RunFrame()
{
    for (TrackerDevice* device : devices)
        device->runFrame();
}

bool ServerDriver::ShouldBlockStandbyMode()
{
    return false;
}

void ServerDriver::EnterStandby()
{
}

void ServerDriver::LeaveStandby()
{
}
