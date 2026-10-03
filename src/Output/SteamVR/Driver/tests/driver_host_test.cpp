// Loads the built driver library and plays the part of vrserver, so the
// driver can be checked without SteamVR. It prints every pose the driver
// publishes and every property it sets.
//
//   driver_host_test <path to driver library> <seconds to run>

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <thread>
#include <vector>

#include <dlfcn.h>

#include "../third_party/openvr/openvr_driver.h"

namespace
{
    std::vector<vr::ITrackedDeviceServerDriver*> devices;
    std::vector<std::string> serials;
}

class MockHost : public vr::IVRServerDriverHost
{
    public:
        bool TrackedDeviceAdded(const char* serial, vr::ETrackedDeviceClass deviceClass, vr::ITrackedDeviceServerDriver* driver) override
        {
            std::uint32_t index = static_cast<std::uint32_t>(devices.size());
            devices.push_back(driver);
            serials.push_back(serial);
            std::printf("ADDED index=%u serial=%s class=%d\n", index, serial, static_cast<int>(deviceClass));
            return driver->Activate(index) == vr::VRInitError_None;
        }

        void TrackedDevicePoseUpdated(std::uint32_t index, const vr::DriverPose_t& pose, std::uint32_t size) override
        {
            std::printf(
                "POSE index=%u serial=%s valid=%d result=%d pos=%.3f,%.3f,%.3f rot(xyzw)=%.3f,%.3f,%.3f,%.3f size_ok=%d\n",
                index, serials[index].c_str(), pose.poseIsValid ? 1 : 0, static_cast<int>(pose.result),
                pose.vecPosition[0], pose.vecPosition[1], pose.vecPosition[2],
                pose.qRotation.x, pose.qRotation.y, pose.qRotation.z, pose.qRotation.w,
                size == sizeof(vr::DriverPose_t) ? 1 : 0);
            std::fflush(stdout);
        }

        void VsyncEvent(double) override {}
        void VendorSpecificEvent(std::uint32_t, vr::EVREventType, const vr::VREvent_Data_t&, double) override {}
        bool IsExiting() override { return false; }
        bool PollNextEvent(vr::VREvent_t*, std::uint32_t) override { return false; }
        void GetRawTrackedDevicePoses(float, vr::TrackedDevicePose_t*, std::uint32_t) override {}
        void RequestRestart(const char*, const char*, const char*, const char*) override {}
        std::uint32_t GetFrameTimings(vr::Compositor_FrameTiming*, std::uint32_t) override { return 0; }
        void SetDisplayEyeToHead(std::uint32_t, const vr::HmdMatrix34_t&, const vr::HmdMatrix34_t&) override {}
        void SetDisplayProjectionRaw(std::uint32_t, const vr::HmdRect2_t&, const vr::HmdRect2_t&) override {}
        void SetRecommendedRenderTargetSize(std::uint32_t, std::uint32_t, std::uint32_t) override {}
};

class MockProperties : public vr::IVRProperties
{
    public:
        vr::ETrackedPropertyError ReadPropertyBatch(vr::PropertyContainerHandle_t, vr::PropertyRead_t*, std::uint32_t) override
        {
            return vr::TrackedProp_Success;
        }

        vr::ETrackedPropertyError WritePropertyBatch(vr::PropertyContainerHandle_t container, vr::PropertyWrite_t* batch, std::uint32_t count) override
        {
            for (std::uint32_t i = 0; i < count; i++)
            {
                if (batch[i].writeType != vr::PropertyWrite_Set)
                    continue;

                if (batch[i].unTag == vr::k_unStringPropertyTag)
                {
                    std::printf("PROP container=%llu prop=%d string=%s\n",
                        static_cast<unsigned long long>(container), static_cast<int>(batch[i].prop),
                        static_cast<const char*>(batch[i].pvBuffer));
                }
            }

            return vr::TrackedProp_Success;
        }

        const char* GetPropErrorNameFromEnum(vr::ETrackedPropertyError) override { return "mock"; }

        vr::PropertyContainerHandle_t TrackedDeviceToPropertyContainer(vr::TrackedDeviceIndex_t index) override
        {
            return 1000 + index;
        }
};

class MockSettings : public vr::IVRSettings
{
    public:
        const char* GetSettingsErrorNameFromEnum(vr::EVRSettingsError) override { return "mock"; }
        void SetBool(const char*, const char*, bool, vr::EVRSettingsError*) override {}
        void SetInt32(const char*, const char*, int32_t, vr::EVRSettingsError*) override {}
        void SetFloat(const char*, const char*, float, vr::EVRSettingsError*) override {}

        void SetString(const char* section, const char* key, const char* value, vr::EVRSettingsError*) override
        {
            std::printf("SETTING [%s] %s = %s\n", section, key, value);
        }

        bool GetBool(const char*, const char*, vr::EVRSettingsError*) override { return false; }

        int32_t GetInt32(const char* section, const char* key, vr::EVRSettingsError* error) override
        {
            if (error != nullptr)
                *error = vr::VRSettingsError_None;

            if (std::strcmp(section, "driver_openfbt") == 0 && std::strcmp(key, "port") == 0)
                return std::getenv("OPENFBT_TEST_PORT") ? std::atoi(std::getenv("OPENFBT_TEST_PORT")) : 43210;

            if (error != nullptr)
                *error = vr::VRSettingsError_ReadFailed;

            return 0;
        }

        float GetFloat(const char*, const char*, vr::EVRSettingsError*) override { return 0.0f; }
        void GetString(const char*, const char*, char* value, uint32_t length, vr::EVRSettingsError*) override { if (length) value[0] = 0; }
        void RemoveSection(const char*, vr::EVRSettingsError*) override {}
        void RemoveKeyInSection(const char*, const char*, vr::EVRSettingsError*) override {}
};

class MockLog : public vr::IVRDriverLog
{
    public:
        void Log(const char* message) override { std::printf("LOG %s", message); }
};

class MockContext : public vr::IVRDriverContext
{
    public:
        void* GetGenericInterface(const char* version, vr::EVRInitError* error) override
        {
            if (error != nullptr)
                *error = vr::VRInitError_None;

            if (std::strcmp(version, vr::IVRServerDriverHost_Version) == 0) return &host;
            if (std::strcmp(version, vr::IVRProperties_Version) == 0) return &properties;
            if (std::strcmp(version, vr::IVRSettings_Version) == 0) return &settings;
            if (std::strcmp(version, vr::IVRDriverLog_Version) == 0) return &log;

            // InitServer only checks that these exist. The driver never calls them.
            if (std::strcmp(version, vr::IVRDriverManager_Version) == 0) return &unused;
            if (std::strcmp(version, vr::IVRResources_Version) == 0) return &unused;

            if (error != nullptr)
                *error = vr::VRInitError_Init_InterfaceNotFound;

            return nullptr;
        }

        vr::DriverHandle_t GetDriverHandle() override { return 1; }

        MockHost host;
        MockProperties properties;
        MockSettings settings;
        MockLog log;
        char unused[64];
};

int main(int argc, char** argv)
{
    if (argc < 3)
        return 2;

    void* library = dlopen(argv[1], RTLD_NOW);

    if (library == nullptr)
    {
        std::printf("FAIL dlopen: %s\n", dlerror());
        return 1;
    }

    typedef void* (*Factory)(const char*, int*);
    Factory factory = reinterpret_cast<Factory>(dlsym(library, "HmdDriverFactory"));

    int code = 0;
    vr::IServerTrackedDeviceProvider* provider = static_cast<vr::IServerTrackedDeviceProvider*>(
        factory(vr::IServerTrackedDeviceProvider_Version, &code));

    if (provider == nullptr)
    {
        std::printf("FAIL factory returned null\n");
        return 1;
    }

    void* wrong = factory("SomethingElse_001", &code);
    std::printf("WRONG_INTERFACE null=%d code=%d\n", wrong == nullptr ? 1 : 0, code);

    MockContext context;

    if (provider->Init(&context) != vr::VRInitError_None)
    {
        std::printf("FAIL Init\n");
        return 1;
    }

    std::printf("INIT ok devices=%zu\n", devices.size());

    auto end = std::chrono::steady_clock::now() + std::chrono::milliseconds(static_cast<int>(std::atof(argv[2]) * 1000));

    while (std::chrono::steady_clock::now() < end)
    {
        provider->RunFrame();
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    provider->Cleanup();

    for (vr::ITrackedDeviceServerDriver* device : devices)
        device->Deactivate();

    std::printf("CLEANUP ok\n");
    return 0;
}
