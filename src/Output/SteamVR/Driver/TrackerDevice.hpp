#pragma once

#include <chrono>
#include <mutex>
#include <string>

#include "third_party/openvr/openvr_driver.h"

#include "Protocol.hpp"

class TrackerDevice final : public vr::ITrackedDeviceServerDriver
{
    public:
        TrackerDevice(int id, const char* serial, const char* controllerType);
        ~TrackerDevice() = default;

        // vr::ITrackedDeviceServerDriver
        vr::EVRInitError Activate(std::uint32_t objectId) override;
        void Deactivate() override;
        void EnterStandby() override;
        void* GetComponent(const char* componentNameAndVersion) override;
        void DebugRequest(const char* request, char* responseBuffer, std::uint32_t responseBufferSize) override;
        vr::DriverPose_t GetPose() override;

        const std::string& getSerial() const;

        // Called from the receive thread for every packet.
        void update(const Protocol::TrackerPacket& packet);

        // Called from RunFrame. Marks the tracker as lost if packets stop.
        void runFrame();

    private:
        void publish(const vr::DriverPose_t& pose);

        int id;
        std::string serial;
        std::string controllerType;

        std::uint32_t objectId;
        bool active;
        bool lost;

        std::mutex mutex;
        std::chrono::steady_clock::time_point lastPacket;
        vr::DriverPose_t lastPose;
};
