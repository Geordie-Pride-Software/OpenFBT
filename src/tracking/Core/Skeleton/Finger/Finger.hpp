#pragma once

#include "../../Joint/Joint.hpp"

class Finger
{
    private:
        Joint base;
        Joint joint;
        Joint tip;

    public:
        Finger(int baseID, int jointID, int tipID, const char* name);
        ~Finger() = default;

        Joint& getBase();
        Joint& getJoint();
        Joint& getTip();
};