#pragma once

#include "Protocol.hpp"

struct TrackerRole
{
    const char* serial;
    const char* steamVrRole;     // value for the "trackers" settings section
    const char* controllerType;  // matches the Vive tracker role names
};

// Index = tracker id used in the UDP packet (and by SteamVrOutput.py).
static const TrackerRole TRACKER_ROLES[Protocol::TRACKER_COUNT] =
{
    { "OpenFBT_Hips",       "TrackerRole_Waist",      "vive_tracker_waist" },
    { "OpenFBT_Chest",      "TrackerRole_Chest",      "vive_tracker_chest" },
    { "OpenFBT_LeftFoot",   "TrackerRole_LeftFoot",   "vive_tracker_left_foot" },
    { "OpenFBT_RightFoot",  "TrackerRole_RightFoot",  "vive_tracker_right_foot" },
    { "OpenFBT_LeftKnee",   "TrackerRole_LeftKnee",   "vive_tracker_left_knee" },
    { "OpenFBT_RightKnee",  "TrackerRole_RightKnee",  "vive_tracker_right_knee" },
    { "OpenFBT_LeftElbow",  "TrackerRole_LeftElbow",  "vive_tracker_left_elbow" },
    { "OpenFBT_RightElbow", "TrackerRole_RightElbow", "vive_tracker_right_elbow" }
};
