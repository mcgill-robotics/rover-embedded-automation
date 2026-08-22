#!/bin/bash

# This script sets up a cli build with CMake for use with the Containerfile

cd $1

# Configure build
# Configure as fresh to remove cache and start fresh in CI
if [[ $2 == "--stm32cubemx" ]];then 
	echo "Configuring CubeMX CMake Project for $(pwd)"
	echo "Using standard arm-none-eabi-gcc toolchain"
	echo ""
	cmake --fresh -DCMAKE_BUILD_TYPE=Debug \
		-DCMAKE_TOOLCHAIN_FILE="./cmake/gcc-arm-none-eabi.cmake" \
		-DCMAKE_COMMAND=cmake \
		-DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=TRUE \
		-S "." -B "./build/Debug" -G Ninja
else
	echo "Configuring Standard CMake Project for $(pwd)"
	echo "Using standard gcc toolchain"
	echo ""
	cmake --fresh -DCMAKE_BUILD_TYPE=Debug \
		-D CMAKE_C_COMPILER=gcc \
		-D CMAKE_CXX_COMPILER=g++ \
		-S "." -B "./build/Debug" -G Ninja
fi 
echo ""

# Actually build
echo "Starting Build for $(pwd)"
echo ""
cmake --build "./build/Debug"