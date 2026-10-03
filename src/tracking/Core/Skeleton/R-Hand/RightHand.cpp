#include "RightHand.hpp"

RightHand::RightHand(int id, const char* name, const Finger& thumb, const Finger& index, const Finger& middle, const Finger& ring, const Finger& little) : Joint(id, name), thumb(thumb), index(index), middle(middle), ring(ring), little(little)
{
}

Finger& RightHand::getThumb()
{
    return thumb;
}

Finger& RightHand::getIndex()
{
    return index;
}

Finger& RightHand::getMiddle()
{
    return middle;
}

Finger& RightHand::getRing()
{
    return ring;
}

Finger& RightHand::getLittle()
{
    return little;
}