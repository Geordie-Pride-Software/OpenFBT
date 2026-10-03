#include "Skeleton.hpp"

namespace
{
    Finger makeFinger(int baseId, const char* name)
    {
        return Finger(baseId, baseId + 1, baseId + 2, name);
    }
}

Skeleton::Skeleton()
    : leftHand(12, "Left Hand",
        makeFinger(13, "Left Thumb"),
        makeFinger(16, "Left Index"),
        makeFinger(19, "Left Middle"),
        makeFinger(22, "Left Ring"),
        makeFinger(25, "Left Little")),
      rightHand(28, "Right Hand",
        makeFinger(29, "Right Thumb"),
        makeFinger(32, "Right Index"),
        makeFinger(35, "Right Middle"),
        makeFinger(38, "Right Ring"),
        makeFinger(41, "Right Little"))
{
}

Chest& Skeleton::getChest()
{
    return chest;
}

Neck& Skeleton::getNeck()
{
    return neck;
}

Waist& Skeleton::getWaist()
{
    return waist;
}

Hips& Skeleton::getHips()
{
    return hips;
}

LeftElbow& Skeleton::getLeftElbow()
{
    return leftElbow;
}

RightElbow& Skeleton::getRightElbow()
{
    return rightElbow;
}

LeftKnee& Skeleton::getLeftKnee()
{
    return leftKnee;
}

RightKnee& Skeleton::getRightKnee()
{
    return rightKnee;
}

LeftFoot& Skeleton::getLeftFoot()
{
    return leftFoot;
}

RightFoot& Skeleton::getRightFoot()
{
    return rightFoot;
}

LeftHand& Skeleton::getLeftHand()
{
    return leftHand;
}

RightHand& Skeleton::getRightHand()
{
    return rightHand;
}