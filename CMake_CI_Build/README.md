# CMake CI Build Runner

Automation scripts and containers for running firmware and library builds in CI.

## ProjectDiscovery.py

This script discovers CMake projets in a directory recursively and builds them.
Builds use gcc-arm-none-eabi for STM32CubeMX projects and standard gcc for libraries
that are not generated using STM32CubeMX. If any build fails, it exits with a non-zero
exit code. To use it, use `python ProjectDiscovery.py <directory>`

## build.sh

The script that configures and builds a CMake project for use as the entrypoint to a container

## Containerfile

Containerfile/Dockerfile designed to support a consistent build environment so we can verify if our firmware compiles. The container this builds is intended to run in a CI environment.

The project to compile should be mounted to `/home/ci-runner/project` in the container.

### Packages

Here is a brief description of the packages installed in the container.

`python3` : To enable more powerful scripting in CMake configuration if necessary.

`cmake` : Libraries and projects depending on them use CMake for builds.

`gcc-arm-none-eabi` : Cross compiling toolchain used for our embedded builds.

`gcc` : To compile libraries that don't directly generate an embedded target binary.

`g++` : To compile libraries that don't directly generate an embedded target binary.

`git` : To pull submodules and other git operation that might be done in the 
cmake configuration stage.

`ninja-build` : Build system CMake will use to setup builds.

`wget` : Used to download dependencies.

`curl` : Alternative to download depencies

`make` : Available as an alternative to Ninja if needed.

`bash` : To run the `build.sh` script.

`libnewlib-dev` : C standard library implementation needed for the embedded targets.
