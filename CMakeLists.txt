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
set(ONNXRUNTIME_DIR $ENV{ONNXRUNTIME_DIR})

set(CONSTANT_MULTIPLICATION_SOURCES
    src/mcm.cpp
    src/mcm_algorithms.cpp
    src/mcm_ilp.cpp
    src/cmvm.cpp
)

add_library(constant_multiplication STATIC ${CONSTANT_MULTIPLICATION_SOURCES})
target_include_directories(constant_multiplication
    PUBLIC
        ${PROJECT_SOURCE_DIR}/src
        ${ORTOOLS_DIR}/include
)
target_link_directories(constant_multiplication PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(constant_multiplication PUBLIC ortools)

# Add the main executable
add_executable(rtlgen main.cpp src/multiplier.cpp src/adder.cpp src/config.cpp src/rtl_operations.cpp)
target_include_directories(rtlgen PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include ${ONNXRUNTIME_DIR}/include ${PROJECT_SOURCE_DIR}/src)
target_link_directories(rtlgen PUBLIC ${ORTOOLS_DIR}/lib ${ONNXRUNTIME_DIR}/lib)
target_link_libraries(rtlgen constant_multiplication ortools onnxruntime)

set (CMAKE_INSTALL_PREFIX ${PROJECT_SOURCE_DIR})
install(TARGETS rtlgen DESTINATION bin)

# Add the test executable
add_executable(test_boolexp tests/test_boolexp.cpp src/multiplier.cpp src/adder.cpp)
target_include_directories(test_boolexp PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include ${PROJECT_SOURCE_DIR}/src)
target_link_directories(test_boolexp PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(test_boolexp ${GTEST_LIBRARIES} GTest::Main pthread ortools)

# Add the test to CTest
add_test(NAME BoolExpTest COMMAND test_boolexp)

# Add the test executable for adder
add_executable(test_adder tests/test_adder.cpp src/adder.cpp)
target_include_directories(test_adder PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include ${PROJECT_SOURCE_DIR}/src)
target_link_directories(test_adder PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(test_adder ${GTEST_LIBRARIES} GTest::Main pthread ortools)

add_executable(test_multiplier tests/test_multiplier.cpp src/multiplier.cpp src/adder.cpp)
target_include_directories(test_multiplier PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include ${PROJECT_SOURCE_DIR}/src)
target_link_directories(test_multiplier PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(test_multiplier ${GTEST_LIBRARIES} GTest::Main pthread ortools)

add_test(NAME test_adder COMMAND test_adder)
add_test(NAME test_multiplier COMMAND test_multiplier)

add_executable(test_onnx tests/test_onnx.cpp src/config.cpp)
target_include_directories(test_onnx PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/json/include ${ONNXRUNTIME_DIR}/include ${PROJECT_SOURCE_DIR}/src)
target_link_directories(test_onnx PUBLIC ${ORTOOLS_DIR}/lib  ${ONNXRUNTIME_DIR}/lib)

target_link_libraries(test_onnx ${GTEST_LIBRARIES} GTest::Main pthread onnxruntime)

add_test(NAME test_onnx COMMAND test_onnx)

add_executable(mcm_cli src/mcm_cli.cpp)
target_link_directories(mcm_cli PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(mcm_cli PRIVATE constant_multiplication)

add_executable(mcm_ilp_cli src/mcm_ilp_cli.cpp)
target_link_directories(mcm_ilp_cli PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(mcm_ilp_cli PRIVATE constant_multiplication)

add_executable(cmvm_cli src/cmvm_cli.cpp)
target_link_directories(cmvm_cli PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(cmvm_cli PRIVATE constant_multiplication)

add_executable(test_mcm_and_cmvm tests/test_mcm_and_cmvm.cpp)
target_link_directories(test_mcm_and_cmvm PUBLIC ${ORTOOLS_DIR}/lib)
target_link_libraries(test_mcm_and_cmvm PRIVATE constant_multiplication ${GTEST_LIBRARIES} GTest::Main pthread)
add_test(NAME test_mcm_and_cmvm COMMAND test_mcm_and_cmvm)

add_test(NAME test_verilog_mcm_and_cmvm COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_verilog_mcm_and_cmvm.sh)
set_tests_properties(test_verilog_mcm_and_cmvm PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_verilog_adder_skew COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_verilog_adder_skew.sh)
set_tests_properties(test_verilog_adder_skew PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
