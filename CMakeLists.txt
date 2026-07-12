cmake_minimum_required(VERSION 3.26)
project(MyBaresipApp LANGUAGES C Swift)

# Find baresip and libre (assuming they are installed on the system)
find_library(BARESIP_LIB baresip REQUIRED)
find_library(LIBRE_LIB re REQUIRED)

# Collect Swift sources
file(GLOB_RECURSE SOURCES src/*.swift)

# Create the executable
add_executable(MyBaresipApp ${SOURCES})

# Expose the module.modulemap to the Swift compiler
target_include_directories(MyBaresipApp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

find_package(OpenSSL REQUIRED)

# Link the C libraries

target_link_libraries(MyBaresipApp PRIVATE
    ${BARESIP_LIB}
    ${LIBRE_LIB}
#    OpenSSL::SSL
#    OpenSSL::Crypto
#    asound
#    opus
#    sndfile
#    X11
#    Xext
#    png
)