cmake_minimum_required(VERSION 3.16)

project(openfbt_driver CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(DRIVER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../src/Output/SteamVR/Driver)

add_library(driver_openfbt SHARED
    ${DRIVER_DIR}/driver_openfbt.cpp
    ${DRIVER_DIR}/ServerDriver.cpp
    ${DRIVER_DIR}/TrackerDevice.cpp
    ${DRIVER_DIR}/UdpReceiver.cpp
    ${DRIVER_DIR}/Protocol.cpp
)

target_include_directories(driver_openfbt PRIVATE ${DRIVER_DIR})

if(WIN32)
    target_link_libraries(driver_openfbt PRIVATE ws2_32)
    set(BIN_FOLDER win64)
else()
    target_link_libraries(driver_openfbt PRIVATE pthread)
    set_target_properties(driver_openfbt PROPERTIES
        CXX_VISIBILITY_PRESET hidden
    )
    set(BIN_FOLDER linux64)
endif()

# SteamVR loads drivers named driver_<name>, with no "lib" prefix.
set_target_properties(driver_openfbt PROPERTIES PREFIX "")

# After building, lay the driver out the way SteamVR expects it:
#   <build>/openfbt/driver.vrdrivermanifest
#   <build>/openfbt/resources/settings/default.vrsettings
#   <build>/openfbt/bin/<win64|linux64>/driver_openfbt.<dll|so>
set(PACKAGE_DIR ${CMAKE_BINARY_DIR}/openfbt)

add_custom_command(TARGET driver_openfbt POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${PACKAGE_DIR}/bin/${BIN_FOLDER}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${PACKAGE_DIR}/resources/settings
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:driver_openfbt> ${PACKAGE_DIR}/bin/${BIN_FOLDER}/
    COMMAND ${CMAKE_COMMAND} -E copy ${DRIVER_DIR}/driver.vrdrivermanifest ${PACKAGE_DIR}/
    COMMAND ${CMAKE_COMMAND} -E copy ${DRIVER_DIR}/resources/settings/default.vrsettings ${PACKAGE_DIR}/resources/settings/
)
