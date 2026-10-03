#pragma once

#include "Chest/Chest.hpp"
#include "Hips/Hips.hpp"
#include "Neck/Neck.hpp"
#include "Waist/Waist.hpp"

#include "L-Elbow/LeftElbow.hpp"
#include "R-Elbow/RightElbow.hpp"

#include "L-Knee/LeftKnee.hpp"
#include "R-Knee/RightKnee.hpp"

#include "L-Foot/LeftFoot.hpp"
#include "R-Foot/RightFoot.hpp"

#include "L-Hand/LeftHand.hpp"
#include "R-Hand/RightHand.hpp"


class Skeleton
{
    private:
        Chest chest;
        Neck neck;
        Waist waist;
        Hips hips;

        LeftElbow leftElbow;
        RightElbow rightElbow;

        LeftKnee leftKnee;
        RightKnee rightKnee;

        LeftFoot leftFoot;
        RightFoot rightFoot;

        LeftHand leftHand;
        RightHand rightHand;

    public:
        Skeleton();
        ~Skeleton() = default;

        Chest& getChest();
        Neck& getNeck();
        Waist& getWaist();
        Hips& getHips();

        LeftElbow& getLeftElbow();
        RightElbow& getRightElbow();

        LeftKnee& getLeftKnee();
        RightKnee& getRightKnee();

        LeftFoot& getLeftFoot();
        RightFoot& getRightFoot();

        LeftHand& getLeftHand();
        RightHand& getRightHand();
};