#include <cstring>

#include "ServerDriver.hpp"

#if defined(_WIN32)
    #define OPENFBT_EXPORT extern "C" __declspec(dllexport)
#else
    #define OPENFBT_EXPORT extern "C" __attribute__((visibility("default")))
#endif

static ServerDriver serverDriver;

OPENFBT_EXPORT void* HmdDriverFactory(const char* interfaceName, int* returnCode)
{
    if (std::strcmp(interfaceName, vr::IServerTrackedDeviceProvider_Version) == 0)
        return &serverDriver;

    if (returnCode != nullptr)
        *returnCode = vr::VRInitError_Init_InterfaceNotFound;

    return nullptr;
}
