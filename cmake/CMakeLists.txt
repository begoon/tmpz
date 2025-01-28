cmake_minimum_required(VERSION 3.10)

project(vanilla-c)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)

find_package(CURL REQUIRED)

add_executable(vanilla-c main.c client.c)

target_link_libraries(vanilla-c CURL::libcurl)
