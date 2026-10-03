#include "Joint.hpp"

Joint::Joint(int id, const char* name) : id(id), name(name), pose()
{
}

int Joint::getID() const
{
    return id;
}

const char* Joint::getName() const
{
    return name;
}

Pose& Joint::getPose()
{
    return pose;
}

const Pose& Joint::getPose() const
{
    return pose;
}