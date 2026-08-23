# CI CMake Discovery

Discover CMake projects and build them using the container at [cmake_build_container](../cmake_build_container/)

## ProjectDiscovery.py

This script discovers CMake projets in a directory recursively and builds them.
Builds use gcc-arm-none-eabi for STM32CubeMX projects and standard gcc for libraries
that are not generated using STM32CubeMX. If any build fails, it exits with a non-zero
exit code. To use it, use `python ProjectDiscovery.py <directory> <container runtime command> <container image>`