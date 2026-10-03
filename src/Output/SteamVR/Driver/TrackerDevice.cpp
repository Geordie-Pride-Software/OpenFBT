#include "TrackerDevice.hpp"

#include <cstring>

namespace
{
    const std::chrono::milliseconds LOST_AFTER(1000);

    vr::DriverPose_t makeBasePose()
    {
        vr::DriverPose_t pose = {};

        pose.qWorldFromDriverRotation.w = 1.0;
        pose.qDriverFromHeadRotation.w = 1.0;
        pose.qRotation.w = 1.0;

        pose.willDriftInYaw = false;
        pose.shouldApplyHeadModel = false;

        return pose;
    }
}

TrackerDevice::TrackerDevice(int id, const char* serial, const char* controllerType)
    : id(id),
      serial(serial),
      controllerType(controllerType),
      objectId(vr::k_unTrackedDeviceIndexInvalid),
      active(false),
      lost(true),
      lastPacket(),
      lastPose(makeBasePose())
{
    lastPose.result = vr::TrackingResult_Uninitialized;
    lastPose.poseIsValid = false;
    lastPose.deviceIsConnected = true;
}

vr::EVRInitError TrackerDevice::Activate(std::uint32_t newObjectId)
{
    objectId = newObjectId;

    vr::PropertyContainerHandle_t container =
        vr::VRProperties()->TrackedDeviceToPropertyContainer(objectId);

    vr::VRProperties()->SetStringProperty(container, vr::Prop_ModelNumber_String, "OpenFBT Tracker");
    vr::VRProperties()->SetStringProperty(container, vr::Prop_ManufacturerName_String, "OpenFBT");
    vr::VRProperties()->SetStringProperty(container, vr::Prop_TrackingSystemName_String, "openfbt");
    vr::VRProperties()->SetStringProperty(container, vr::Prop_SerialNumber_String, serial.c_str());

    std::string registered = "openfbt/" + serial;
    vr::VRProperties()->SetStringProperty(container, vr::Prop_RegisteredDeviceType_String, registered.c_str());

    vr::VRProperties()->SetStringProperty(container, vr::Prop_ControllerType_String, controllerType.c_str());
    vr::VRProperties()->SetStringProperty(container, vr::Prop_InputProfilePath_String, "{htc}/input/vive_tracker_profile.json");
    vr::VRProperties()->SetStringProperty(container, vr::Prop_RenderModelName_String, "{htc}vr_tracker_vive_1_0");

    vr::VRProperties()->SetBoolProperty(container, vr::Prop_NeverTracked_Bool, false);
    vr::VRProperties()->SetBoolProperty(container, vr::Prop_WillDriftInYaw_Bool, false);
    vr::VRProperties()->SetBoolProperty(container, vr::Prop_DeviceIsWireless_Bool, true);
    vr::VRProperties()->SetBoolProperty(container, vr::Prop_DeviceProvidesBatteryStatus_Bool, false);

    {
        std::lock_guard<std::mutex> lock(mutex);
        active = true;
        lost = true;
    }

    return vr::VRInitError_None;
}

void TrackerDevice::Deactivate()
{
    std::lock_guard<std::mutex> lock(mutex);

    active = false;
    objectId = vr::k_unTrackedDeviceIndexInvalid;
}

void TrackerDevice::EnterStandby()
{
}

void* TrackerDevice::GetComponent(const char*)
{
    return nullptr;
}

void TrackerDevice::DebugRequest(const char*, char* responseBuffer, std::uint32_t responseBufferSize)
{
    if (responseBufferSize >= 1)
        responseBuffer[0] = '\0';
}

vr::DriverPose_t TrackerDevice::GetPose()
{
    std::lock_guard<std::mutex> lock(mutex);
    return lastPose;
}

const std::string& TrackerDevice::getSerial() const
{
    return serial;
}

void TrackerDevice::update(const Protocol::TrackerPacket& packet)
{
    std::lock_guard<std::mutex> lock(mutex);

    if (!active)
        return;

    vr::DriverPose_t pose = makeBasePose();

    pose.vecPosition[0] = packet.position[0];
    pose.vecPosition[1] = packet.position[1];
    pose.vecPosition[2] = packet.position[2];

    // Packet order is x, y, z, w. OpenVR wants w first.
    pose.qRotation.x = packet.rotation[0];
    pose.qRotation.y = packet.rotation[1];
    pose.qRotation.z = packet.rotation[2];
    pose.qRotation.w = packet.rotation[3];

    pose.poseIsValid = packet.valid;
    pose.result = packet.valid
        ? vr::TrackingResult_Running_OK
        : vr::TrackingResult_Running_OutOfRange;
    pose.deviceIsConnected = true;

    lastPose = pose;
    lastPacket = std::chrono::steady_clock::now();
    lost = false;

    publish(pose);
}

void TrackerDevice::runFrame()
{
    std::lock_guard<std::mutex> lock(mutex);

    if (!active || lost)
        return;

    if (std::chrono::steady_clock::now() - lastPacket < LOST_AFTER)
        return;

    lost = true;

    lastPose.poseIsValid = false;
    lastPose.result = vr::TrackingResult_Running_OutOfRange;

    publish(lastPose);
}

void TrackerDevice::publish(const vr::DriverPose_t& pose)
{
    // The caller holds the mutex.
    if (objectId == vr::k_unTrackedDeviceIndexInvalid)
        return;

    vr::VRServerDriverHost()->TrackedDevicePoseUpdated(objectId, pose, sizeof(vr::DriverPose_t));
}
