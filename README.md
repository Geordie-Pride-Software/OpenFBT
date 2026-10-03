# OpenFBT

Full body tracking from one webcam. MediaPipe finds your pose, a solver turns it into eight body trackers (hips, chest, feet, knees, elbows), and they are sent to SteamVR through a small driver, or to VRChat over OSC.

## Running the Python app

Install the packages in requirements.txt, then run `python -m src.main` from the repo root. Stand upright with your feet in view and press C to calibrate. Press Q to quit. The default output is the SteamVR driver. Use `--output osc` for VRChat OSC trackers or `--output both` for both.

## Building the SteamVR driver

The driver is a C++ library in `src/Output/SteamVR/Driver`. It needs CMake and a C++17 compiler (Visual Studio on Windows). Run `cmake -S make -B build` and then `cmake --build build --config Release`. The build leaves a ready folder at `build/openfbt` with the manifest, settings and library laid out the way SteamVR expects.

Register that folder with SteamVR by running `vrpathreg adddriver <full path to build/openfbt>` (vrpathreg lives in SteamVR's `bin/win64` folder), or copy the folder into SteamVR's `drivers` folder. Start SteamVR, then start the Python app. Eight trackers appear in SteamVR with waist, chest, foot, knee and elbow roles. They are marked lost if packets stop for a second.

The driver listens on UDP port 43210 on localhost. Change it in `resources/settings/default.vrsettings` and pass `--steamvr-port` to the app to match.

## Tests

`python -m unittest tests.test_openfbt` runs the Python tests. `src/Output/SteamVR/Driver/tests/driver_host_test.cpp` loads the built driver on Linux and plays the part of vrserver, which is how the driver was checked without SteamVR.
