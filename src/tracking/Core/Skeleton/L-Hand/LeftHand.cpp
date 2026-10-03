#include "LeftHand.hpp"

LeftHand::LeftHand(int id, const char* name, const Finger& thumb, const Finger& index, const Finger& middle, const Finger& ring, const Finger& little) : Joint(id, name), thumb(thumb), index(index), middle(middle), ring(ring), little(little)
{
}

Finger& LeftHand::getThumb()
{
    return thumb;
}

Finger& LeftHand::getIndex()
{
    return index;
}

Finger& LeftHand::getMiddle()
{
    return middle;
}

Finger& LeftHand::getRing()
{
    return ring;
}

Finger& LeftHand::getLittle()
{
    return little;
}