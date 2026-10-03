#pragma once

#include <memory>
#include <vector>

#include "third_party/openvr/openvr_driver.h"

#include "TrackerDevice.hpp"
#include "UdpReceiver.hpp"

class ServerDriver : public vr::IServerTrackedDeviceProvider
{
    public:
        vr::EVRInitError Init(vr::IVRDriverContext* driverContext) override;
        void Cleanup() override;
        const char* const* GetInterfaceVersions() override;
        void RunFrame() override;
        bool ShouldBlockStandbyMode() override;
        void EnterStandby() override;
        void LeaveStandby() override;

    private:
        // The devices are owned by SteamVR once added, so only keep pointers.
        std::vector<TrackerDevice*> devices;
        UdpReceiver receiver;
};
