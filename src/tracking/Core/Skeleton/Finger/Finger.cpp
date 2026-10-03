#include "Finger.hpp"

Finger::Finger(int baseID, int jointID, int tipID, const char* name) : base(baseID, name), joint(jointID, name), tip(tipID, name)
{
}

Joint& Finger::getBase()
{
    return base;
}

Joint& Finger::getJoint()
{
    return joint;
}

Joint& Finger::getTip()
{
    return tip;
}