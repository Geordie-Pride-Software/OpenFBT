#pragma once

#include "../../Joint/Joint.hpp"
#include "../Finger/Finger.hpp"

class LeftHand : public Joint
{
    private:
        Finger thumb;
        Finger index;
        Finger middle;
        Finger ring;
        Finger little;

    public:
        LeftHand(int id, const char* name, const Finger& thumb, const Finger& index, const Finger& middle, const Finger& ring, const Finger& little);
        ~LeftHand() = default;

        Finger& getThumb();
        Finger& getIndex();
        Finger& getMiddle();
        Finger& getRing();
        Finger& getLittle();
};