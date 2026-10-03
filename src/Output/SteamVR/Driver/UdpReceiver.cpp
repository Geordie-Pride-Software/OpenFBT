#include "UdpReceiver.hpp"

#include <cstdint>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    typedef int SocketLength;
    static const unsigned long long INVALID_HANDLE = INVALID_SOCKET;
#else
    #include <arpa/inet.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <sys/time.h>
    #include <unistd.h>
    typedef socklen_t SocketLength;
    static const int INVALID_HANDLE = -1;
#endif

UdpReceiver::UdpReceiver()
    : running(false), socketHandle(INVALID_HANDLE)
{
}

UdpReceiver::~UdpReceiver()
{
    stop();
}

bool UdpReceiver::start(int port, Callback cb)
{
    if (running)
        return false;

#ifdef _WIN32
    WSADATA wsaData;

    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
        return false;
#endif

    socketHandle = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    if (socketHandle == INVALID_HANDLE)
        return false;

    sockaddr_in address = {};
    address.sin_family = AF_INET;
    address.sin_port = htons(static_cast<std::uint16_t>(port));
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (bind(socketHandle, reinterpret_cast<sockaddr*>(&address), sizeof(address)) != 0)
    {
        stop();
        return false;
    }

    // A receive timeout lets the thread notice when it is asked to stop.
#ifdef _WIN32
    DWORD timeout = 100;
    setsockopt(socketHandle, SOL_SOCKET, SO_RCVTIMEO,
        reinterpret_cast<const char*>(&timeout), sizeof(timeout));
#else
    timeval timeout = {};
    timeout.tv_usec = 100 * 1000;
    setsockopt(socketHandle, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
#endif

    callback = cb;
    running = true;
    thread = std::thread(&UdpReceiver::run, this);

    return true;
}

void UdpReceiver::stop()
{
    running = false;

    if (thread.joinable())
        thread.join();

    if (socketHandle != INVALID_HANDLE)
    {
#ifdef _WIN32
        closesocket(socketHandle);
        WSACleanup();
#else
        close(socketHandle);
#endif
        socketHandle = INVALID_HANDLE;
    }
}

void UdpReceiver::run()
{
    std::uint8_t buffer[512];

    while (running)
    {
        int received = static_cast<int>(recv(
            socketHandle,
            reinterpret_cast<char*>(buffer),
            sizeof(buffer),
            0
        ));

        if (received <= 0)
            continue;

        Protocol::TrackerPacket packet;

        if (Protocol::parse(buffer, static_cast<std::size_t>(received), packet))
            callback(packet);
    }
}
