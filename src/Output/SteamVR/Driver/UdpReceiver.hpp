#pragma once

#include <atomic>
#include <functional>
#include <thread>

#include "Protocol.hpp"

class UdpReceiver
{
    public:
        typedef std::function<void(const Protocol::TrackerPacket&)> Callback;

        UdpReceiver();
        ~UdpReceiver();

        // Binds to 127.0.0.1:port and starts the receive thread.
        bool start(int port, Callback callback);
        void stop();

    private:
        void run();

        std::atomic<bool> running;
        std::thread thread;
        Callback callback;

#ifdef _WIN32
        unsigned long long socketHandle;
#else
        int socketHandle;
#endif
};
