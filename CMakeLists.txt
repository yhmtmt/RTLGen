cmake_minimum_required(VERSION 3.10)
project(RTLGen)

set(CMAKE_CXX_STANDARD 17)

include(ExternalProject)

option(RTLGEN_BUILD_FLOPOCO "Enable FloPoCo-backed floating-point generator support" ON)
option(RTLGEN_USE_SYSTEM_FLOPOCO "Use an installed/provisioned FloPoCo binary before falling back to bundled sources" ON)
option(RTLGEN_BUILD_FLOPOCO_FROM_SOURCE "Build bundled FloPoCo/PAGSuite from third_party sources" OFF)
option(RTLGEN_BUILD_CACTI "Build the bundled CACTI SRAM estimator" ON)

# Enable testing
enable_testing()

# Add Google Test
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

# Add OR-Tools
set(ORTOOLS_DIR "" CACHE PATH "OR-Tools install prefix (contains include/ and lib/ or lib64/)")
if(NOT ORTOOLS_DIR)
    if(DEFINED ENV{ORTOOLS_DIR} AND NOT "$ENV{ORTOOLS_DIR}" STREQUAL "")
        set(ORTOOLS_DIR "$ENV{ORTOOLS_DIR}")
    elseif(EXISTS "/usr/local/include/ortools")
        set(ORTOOLS_DIR "/usr/local")
    elseif(EXISTS "/home/yhmtmt/work/or-tools_x86_64_Ubuntu-22.04_cpp_v9.10.4067/include/ortools")
        set(ORTOOLS_DIR "/home/yhmtmt/work/or-tools_x86_64_Ubuntu-22.04_cpp_v9.10.4067")
    endif()
endif()

if(NOT ORTOOLS_DIR)
    message(FATAL_ERROR "ORTOOLS_DIR not set. Set env ORTOOLS_DIR or pass -DORTOOLS_DIR=/path/to/or-tools.")
endif()
if(NOT EXISTS "${ORTOOLS_DIR}/include/ortools")
    message(FATAL_ERROR "ORTOOLS_DIR='${ORTOOLS_DIR}' is invalid: missing ${ORTOOLS_DIR}/include/ortools")
endif()

if(EXISTS "${ORTOOLS_DIR}/lib")
    set(ORTOOLS_LIB_DIR "${ORTOOLS_DIR}/lib")
elseif(EXISTS "${ORTOOLS_DIR}/lib64")
    set(ORTOOLS_LIB_DIR "${ORTOOLS_DIR}/lib64")
else()
    message(FATAL_ERROR "ORTOOLS_DIR='${ORTOOLS_DIR}' is invalid: missing lib/ or lib64/")
endif()
set(ONNXRUNTIME_DIR $ENV{ONNXRUNTIME_DIR})

set(CONSTANT_MULTIPLICATION_SOURCES
    src/algorithms/mcm.cpp
    src/algorithms/mcm_algorithms.cpp
    src/algorithms/mcm_ilp.cpp
    src/algorithms/cmvm.cpp
)

add_library(constant_multiplication STATIC ${CONSTANT_MULTIPLICATION_SOURCES})
target_include_directories(constant_multiplication
    PUBLIC
        ${PROJECT_SOURCE_DIR}/src/algorithms
        ${ORTOOLS_DIR}/include
)
target_link_directories(constant_multiplication PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(constant_multiplication PUBLIC ortools)

# Add the main executable
add_executable(rtlgen apps/rtlgen_main.cpp src/rtlgen/multiplier.cpp src/rtlgen/adder.cpp src/rtlgen/config.cpp src/rtlgen/rtl_operations.cpp)
target_include_directories(rtlgen PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/third_party/nlohmann_json/include ${ONNXRUNTIME_DIR}/include ${PROJECT_SOURCE_DIR}/src/rtlgen ${PROJECT_SOURCE_DIR}/src/algorithms)
target_link_directories(rtlgen PUBLIC ${ORTOOLS_LIB_DIR} ${ONNXRUNTIME_DIR}/lib)
target_link_libraries(rtlgen constant_multiplication ortools onnxruntime)

set (CMAKE_INSTALL_PREFIX ${PROJECT_SOURCE_DIR})
install(TARGETS rtlgen DESTINATION bin)

if(RTLGEN_BUILD_CACTI)
    set(CACTI_SOURCE_DIR ${PROJECT_SOURCE_DIR}/third_party/cacti)
    ExternalProject_Add(cacti
        SOURCE_DIR ${CACTI_SOURCE_DIR}
        CONFIGURE_COMMAND ""
        BUILD_COMMAND ${CMAKE_COMMAND} -E env make -C <SOURCE_DIR>
        INSTALL_COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_SOURCE_DIR}/bin
                      COMMAND ${CMAKE_COMMAND} -E copy <SOURCE_DIR>/cacti ${PROJECT_SOURCE_DIR}/bin/cacti
                      COMMAND ${CMAKE_COMMAND} -E remove -f <SOURCE_DIR>/cacti <SOURCE_DIR>/cache.cfg.out
                      COMMAND ${CMAKE_COMMAND} -E remove_directory <SOURCE_DIR>/obj_dbg
        BUILD_IN_SOURCE 1
    )

    add_custom_target(cacti_tool ALL DEPENDS cacti)
endif()

# Add the test executable
add_executable(test_boolexp tests/test_boolexp.cpp src/rtlgen/multiplier.cpp src/rtlgen/adder.cpp)
target_include_directories(test_boolexp PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/third_party/nlohmann_json/include ${PROJECT_SOURCE_DIR}/src/rtlgen)
target_link_directories(test_boolexp PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(test_boolexp ${GTEST_LIBRARIES} GTest::Main pthread ortools)

# Add the test to CTest
add_test(NAME BoolExpTest COMMAND test_boolexp)

# Add the test executable for adder
add_executable(test_adder tests/test_adder.cpp src/rtlgen/adder.cpp)
target_include_directories(test_adder PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/third_party/nlohmann_json/include ${PROJECT_SOURCE_DIR}/src/rtlgen)
target_link_directories(test_adder PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(test_adder ${GTEST_LIBRARIES} GTest::Main pthread ortools)

add_executable(test_multiplier tests/test_multiplier.cpp src/rtlgen/multiplier.cpp src/rtlgen/adder.cpp)
target_include_directories(test_multiplier PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/third_party/nlohmann_json/include ${PROJECT_SOURCE_DIR}/src/rtlgen)
target_link_directories(test_multiplier PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(test_multiplier ${GTEST_LIBRARIES} GTest::Main pthread ortools)

add_test(NAME test_adder COMMAND test_adder)
add_test(NAME test_multiplier COMMAND test_multiplier)

add_executable(test_onnx tests/test_onnx.cpp src/rtlgen/config.cpp)
target_include_directories(test_onnx PUBLIC ${ORTOOLS_DIR}/include ${PROJECT_SOURCE_DIR}/third_party/nlohmann_json/include ${ONNXRUNTIME_DIR}/include ${PROJECT_SOURCE_DIR}/src/rtlgen)
target_link_directories(test_onnx PUBLIC ${ORTOOLS_LIB_DIR}  ${ONNXRUNTIME_DIR}/lib)
target_compile_definitions(test_onnx PRIVATE TEST_ONNX_MODEL_PATH=\"${PROJECT_SOURCE_DIR}/tests/fixtures/test_model.onnx\")
target_link_libraries(test_onnx ${GTEST_LIBRARIES} GTest::Main pthread onnxruntime)

add_test(NAME test_onnx COMMAND test_onnx)

add_executable(mcm_cli apps/mcm_cli.cpp)
target_link_directories(mcm_cli PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(mcm_cli PRIVATE constant_multiplication)

add_executable(mcm_ilp_cli apps/mcm_ilp_cli.cpp)
target_link_directories(mcm_ilp_cli PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(mcm_ilp_cli PRIVATE constant_multiplication)

add_executable(cmvm_cli apps/cmvm_cli.cpp)
target_link_directories(cmvm_cli PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(cmvm_cli PRIVATE constant_multiplication)

add_executable(test_mcm_and_cmvm tests/test_mcm_and_cmvm.cpp)
target_link_directories(test_mcm_and_cmvm PUBLIC ${ORTOOLS_LIB_DIR})
target_link_libraries(test_mcm_and_cmvm PRIVATE constant_multiplication ${GTEST_LIBRARIES} GTest::Main pthread)
add_test(NAME test_mcm_and_cmvm COMMAND test_mcm_and_cmvm)

add_test(NAME test_verilog_mcm_and_cmvm COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_verilog_mcm_and_cmvm.sh)
set_tests_properties(test_verilog_mcm_and_cmvm PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_verilog_adder_skew COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_verilog_adder_skew.sh)
set_tests_properties(test_verilog_adder_skew PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_verilog_fp_mul COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_fp_mul.sh)
set_tests_properties(test_verilog_fp_mul PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_verilog_fp_add COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_fp_add.sh)
set_tests_properties(test_verilog_fp_add PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_verilog_fp_mac COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_fp_mac.sh)
set_tests_properties(test_verilog_fp_mac PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_activation_int COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_activation_int.sh)
set_tests_properties(test_activation_int PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_activation_fp COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_activation_fp.sh)
set_tests_properties(test_activation_fp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_softmax_rowwise COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_softmax_rowwise.sh)
set_tests_properties(test_softmax_rowwise PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

add_test(NAME test_mac_pp_feedback COMMAND bash ${PROJECT_SOURCE_DIR}/tests/test_mac_pp_feedback.sh)
set_tests_properties(test_mac_pp_feedback PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

if(RTLGEN_BUILD_FLOPOCO)
    set(FLOPOCO_STAGED_BIN ${PROJECT_SOURCE_DIR}/bin/flopoco)
    set(FLOPOCO_READY OFF)

    if(RTLGEN_USE_SYSTEM_FLOPOCO)
        find_program(FLOPOCO_SYSTEM_BIN NAMES flopoco)
        if(FLOPOCO_SYSTEM_BIN)
            get_filename_component(FLOPOCO_SYSTEM_BIN_ABS "${FLOPOCO_SYSTEM_BIN}" ABSOLUTE)
            get_filename_component(FLOPOCO_STAGED_BIN_DIR "${FLOPOCO_STAGED_BIN}" DIRECTORY)
            if(FLOPOCO_SYSTEM_BIN_ABS STREQUAL FLOPOCO_STAGED_BIN)
                add_custom_target(flopoco_stage
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${FLOPOCO_STAGED_BIN_DIR}
                    COMMENT "Using provisioned FloPoCo at ${FLOPOCO_SYSTEM_BIN_ABS}"
                )
            else()
                add_custom_target(flopoco_stage
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${FLOPOCO_STAGED_BIN_DIR}
                    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${FLOPOCO_SYSTEM_BIN_ABS} ${FLOPOCO_STAGED_BIN}
                    COMMENT "Staging provisioned FloPoCo from ${FLOPOCO_SYSTEM_BIN_ABS}"
                )
            endif()
            add_custom_target(flopoco_tool ALL DEPENDS flopoco_stage)
            add_dependencies(rtlgen flopoco_stage)
            set(FLOPOCO_READY ON)
        endif()
    endif()

    if(NOT FLOPOCO_READY AND RTLGEN_BUILD_FLOPOCO_FROM_SOURCE)
        find_path(GMP_INCLUDE_DIR gmp.h)
        find_path(GMPXX_INCLUDE_DIR gmpxx.h)
        find_library(GMP_LIBRARY gmp)
        find_library(GMPXX_LIBRARY gmpxx)
        find_path(MPFR_INCLUDE_DIR mpfr.h)
        find_library(MPFR_LIBRARY mpfr)
        find_path(MPFI_INCLUDE_DIR mpfi.h)
        find_library(MPFI_LIBRARY mpfi)
        find_path(SOLLYA_INCLUDE_DIR sollya.h)
        find_library(SOLLYA_LIBRARY sollya)
        find_package(LAPACK QUIET)

        set(FLOPOCO_SOURCE_DEPS_FOUND ON)
        foreach(dep
                GMP_INCLUDE_DIR
                GMPXX_INCLUDE_DIR
                GMP_LIBRARY
                GMPXX_LIBRARY
                MPFR_INCLUDE_DIR
                MPFR_LIBRARY
                MPFI_INCLUDE_DIR
                MPFI_LIBRARY
                SOLLYA_INCLUDE_DIR
                SOLLYA_LIBRARY)
            if(NOT ${dep})
                set(FLOPOCO_SOURCE_DEPS_FOUND OFF)
            endif()
        endforeach()
        if(NOT LAPACK_FOUND)
            set(FLOPOCO_SOURCE_DEPS_FOUND OFF)
        endif()

        if(NOT FLOPOCO_SOURCE_DEPS_FOUND)
            message(WARNING "Bundled FloPoCo build skipped: missing GMP/MPFR/MPFI/LAPACK/Sollya headers or libraries (install libgmp-dev, libmpfr-dev, libmpfi-dev, liblapack-dev, libsollya-dev or equivalents) then re-enable RTLGEN_BUILD_FLOPOCO_FROM_SOURCE.")
        else()
            set(PAGSUITE_SOURCE_DIR ${PROJECT_SOURCE_DIR}/third_party/pagsuite)
            set(PAGSUITE_BINARY_DIR ${CMAKE_BINARY_DIR}/pagsuite-build)
            set(PAGSUITE_INSTALL_DIR ${PROJECT_SOURCE_DIR}/third_party/pagsuite-install)

            ExternalProject_Add(pagsuite
                SOURCE_DIR ${PAGSUITE_SOURCE_DIR}
                BINARY_DIR ${PAGSUITE_BINARY_DIR}
                CMAKE_ARGS
                    -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
                    -DCMAKE_INSTALL_PREFIX=${PAGSUITE_INSTALL_DIR}
                BUILD_COMMAND ${CMAKE_COMMAND} --build <BINARY_DIR>
                INSTALL_COMMAND ${CMAKE_COMMAND} --build <BINARY_DIR> --target install
            )

            set(FLOPOCO_SOURCE_DIR ${PROJECT_SOURCE_DIR}/third_party/flopoco)
            set(FLOPOCO_BINARY_DIR ${CMAKE_BINARY_DIR}/flopoco-build)
            set(FLOPOCO_INSTALL_DIR ${PROJECT_SOURCE_DIR}/third_party/flopoco-install)
            set(FLOPOCO_GIT_HASH_OVERRIDE "\"unknown\"")

            ExternalProject_Add(flopoco
                SOURCE_DIR ${FLOPOCO_SOURCE_DIR}
                BINARY_DIR ${FLOPOCO_BINARY_DIR}
                CMAKE_ARGS
                    -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
                    -DCMAKE_INSTALL_PREFIX=${FLOPOCO_INSTALL_DIR}
                    -DCMAKE_PREFIX_PATH=${PAGSUITE_INSTALL_DIR}
                    -DPAG_LOCAL=${PAGSUITE_INSTALL_DIR}
                    -DPAGSUITE_LOCALLY_BUILT=ON
                    -DFLOPOCO_GIT_HASH=${FLOPOCO_GIT_HASH_OVERRIDE}
                BUILD_COMMAND ${CMAKE_COMMAND} --build <BINARY_DIR>
                INSTALL_COMMAND ${CMAKE_COMMAND} --build <BINARY_DIR> --target install
                PATCH_COMMAND patch -p1 -d <SOURCE_DIR> -i ${PROJECT_SOURCE_DIR}/patches/flopoco-local.patch -N
            )

            ExternalProject_Add_Step(flopoco copy_to_bin
                DEPENDEES install
                COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_SOURCE_DIR}/bin
                COMMAND ${CMAKE_COMMAND} -E copy_if_different ${FLOPOCO_INSTALL_DIR}/bin/flopoco ${FLOPOCO_STAGED_BIN}
            )

            add_custom_target(pagsuite_lib ALL DEPENDS pagsuite)
            add_custom_target(flopoco_tool ALL DEPENDS flopoco)
            add_dependencies(flopoco pagsuite)
            add_dependencies(rtlgen flopoco)
            set(FLOPOCO_READY ON)
        endif()
    endif()

    if(NOT FLOPOCO_READY)
        message(WARNING "FloPoCo support enabled, but no provisioned binary was found on PATH and bundled source build is disabled. Set FLOPOCO_BIN, install flopoco in the container image, or enable RTLGEN_BUILD_FLOPOCO_FROM_SOURCE.")
    endif()
endif()
