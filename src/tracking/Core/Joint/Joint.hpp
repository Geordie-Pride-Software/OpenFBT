#pragma once

#include "../Pose/Pose.hpp"

class Joint
{
    private:
        int id;
        const char* name;
        Pose pose;

    public:
        Joint(int id, const char* name);
        ~Joint() = default;

        int getID() const;
        const char* getName() const;

        Pose& getPose();
        const Pose& getPose() const;
};