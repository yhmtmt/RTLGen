cmake_minimum_required(VERSION 3.10)
project(RTLGen)

set(CMAKE_CXX_STANDARD 17)

# Enable testing
enable_testing()

# Add Google Test
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

# Add OR-Tools
set(ORTOOLS_DIR /home/yhmtmt/work/or-tools_x86_64_Ubuntu-22.04_cpp_v9.10.4067)

# Add the main executable
add_executable(rtlgen main.cpp multiplier.cpp adder.cpp)
target_include_directories(rtlgen PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include)
target_link_directories(rtlgen PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(rtlgen ortools)

set (CMAKE_INSTALL_PREFIX ${PROJECT_SOURCE_DIR})
install(TARGETS rtlgen DESTINATION bin)

# Add the test executable
add_executable(test_boolexp test_boolexp.cpp multiplier.cpp adder.cpp)
target_include_directories(test_boolexp PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include)
target_link_directories(test_boolexp PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(test_boolexp ${GTEST_LIBRARIES} GTest::Main pthread ortools)

# Add the test to CTest
add_test(NAME BoolExpTest COMMAND test_boolexp)

# Add the test executable for adder
add_executable(test_adder test_adder.cpp adder.cpp)
target_include_directories(test_adder PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include)
target_link_directories(test_adder PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(test_adder ${GTEST_LIBRARIES} GTest::Main pthread ortools)

add_executable(test_multiplier test_multiplier.cpp multiplier.cpp adder.cpp)
target_include_directories(test_multiplier PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include)
target_link_directories(test_multiplier PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(test_multiplier ${GTEST_LIBRARIES} GTest::Main pthread ortools)

add_test(NAME test_adder COMMAND test_adder)
add_test(NAME test_multiplier COMMAND test_multiplier)
