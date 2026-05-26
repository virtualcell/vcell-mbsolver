cmake_minimum_required(VERSION 3.13)
project(VCellMovingBoundary VERSION 1.0.0 LANGUAGES CXX C)

# C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Default build type for single-config generators
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Options
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
option(VARIABLE_SPECIES_STORAGE "Dynamic species storage" OFF)
option(OPTION_TARGET_MESSAGING "Enable job-status messaging via CURL" OFF)

if(VARIABLE_SPECIES_STORAGE)
    add_compile_definitions(MB_VARY_MASS)
endif()

# Platform-specific settings
if(MSVC)
    add_compile_definitions(
        HAVE_UNISTD_H=0
        NOMINMAX
        _CRT_SECURE_NO_WARNINGS
    )
elseif(APPLE)
    execute_process(COMMAND uname -m OUTPUT_VARIABLE PROCESSOR_ARCHITECTURE OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(PROCESSOR_ARCHITECTURE STREQUAL "arm64")
        add_compile_definitions(__arm64__)
        set(CMAKE_OSX_ARCHITECTURES "arm64")
    else()
        add_compile_definitions(__x86_64__)
        set(CMAKE_OSX_ARCHITECTURES "x86_64")
    endif()
    add_compile_options(-fpermissive)
elseif(UNIX)
    add_compile_options(-fpermissive)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
        add_compile_options(-m64)
    endif()
endif()

# Required packages
find_package(Threads REQUIRED)
find_package(HDF5 REQUIRED COMPONENTS C CXX)
if(NOT HDF5_FOUND)
    message(FATAL_ERROR "HDF5 not found. Please ensure libhdf5-dev is installed.")
endif()
find_package(Boost REQUIRED)

# Python bindings (always built)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 CONFIG REQUIRED)

# --- Bundled / external library dependencies ---

# FronTier (bundled in FronTierLib/)
add_subdirectory(FronTierLib)

# ExpressionParser (bundled in ExpressionParser/)
add_subdirectory(ExpressionParser)

# vcommons (bundled in vcommons/)
add_subdirectory(vcommons)

# VCellMessaging (bundled in VCellMessaging/)
add_subdirectory(VCellMessaging)

# SQLite: prefer system, fall back to bundled copy in sqlite/
find_file(SYSTEM_SQLITE3_H sqlite3.h)
if(SYSTEM_SQLITE3_H)
    get_filename_component(SQLITE3_INCLUDE_DIR "${SYSTEM_SQLITE3_H}" DIRECTORY)
    message(STATUS "sqlite3:           ${SYSTEM_SQLITE3_H} (system)")
else()
    set(SQLITE3_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/sqlite)
    message(STATUS "sqlite3:           bundled (${SQLITE3_INCLUDE_DIR})")
endif()

message(STATUS "Platform:          ${CMAKE_SYSTEM_NAME}")
message(STATUS "Build type:        ${CMAKE_BUILD_TYPE}")
message(STATUS "HDF5 version:      ${HDF5_VERSION}, libs: ${HDF5_LIBRARIES}")

# --- Source files ---
file(GLOB MB_SOLVER_MAIN  Solver/src/driver.cpp)
file(GLOB MB_ALLOC_MAIN   Solver/src/alloctestmain.cpp)
file(GLOB MB_SRC_FILES    Solver/src/*.cpp)
list(REMOVE_ITEM MB_SRC_FILES ${MB_SOLVER_MAIN} ${MB_ALLOC_MAIN})

# --- Library target ---
add_library(MovingBoundaryLib ${MB_SRC_FILES})

target_include_directories(MovingBoundaryLib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/Solver/include>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/Solver/include/MBridge>
        $<BUILD_INTERFACE:${SQLITE3_INCLUDE_DIR}>
        ${HDF5_INCLUDE_DIRS}
        ${Boost_INCLUDE_DIRS}
        $<INSTALL_INTERFACE:include/vcell-mbsolver>
)

target_link_libraries(MovingBoundaryLib
    PUBLIC
        ${HDF5_LIBRARIES}
        ${HDF5_HL_LIBRARIES}
        frontier
        ExpressionParser
        vcommons
        vcellmessaging
        Threads::Threads
)

# --- Executable target ---
add_executable(MovingBoundarySolver ${MB_SOLVER_MAIN})
target_link_libraries(MovingBoundarySolver PRIVATE MovingBoundaryLib)

# --- Testing ---
include(CTest)
if(BUILD_TESTING)
    add_subdirectory(Tests)
    add_subdirectory(ExpressionParserTest)
endif()

# --- Python bindings ---
add_subdirectory(python)

# --- Install ---
install(TARGETS MovingBoundaryLib MovingBoundarySolver
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
install(DIRECTORY Solver/include/
    DESTINATION include/vcell-mbsolver
    FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp"
)
