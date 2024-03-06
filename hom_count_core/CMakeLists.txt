cmake_minimum_required(VERSION 3.24)
project(hom_count_core)

set(CMAKE_CXX_STANDARD 17)

find_package(Boost REQUIRED)

add_executable(hom_count_core main.cpp
        graph_utils.cpp
        graph_utils.h)

target_link_libraries(hom_count_core ${Boost_LIBRARIES})
include_directories(${Boost_INCLUDE_DIRS})
