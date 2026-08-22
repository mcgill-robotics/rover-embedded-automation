import glob
import pathlib
import subprocess
import re
import sys
import shutil

if len(sys.argv) < 2:
	print("No directory to scan was provided")
	exit(1)
if len(sys.argv) < 3:
	print("No runner container image was provided")
	exit(1)

dir_to_search = pathlib.Path(sys.argv[1])
container_image = sys.argv[2]
def find_mx_projects(repo_path:pathlib.Path) -> list[pathlib.Path]:
	projects = []
	res = glob.glob("**/**.ioc", root_dir=repo_path, recursive=True)
	for path in res:
		projects.append(pathlib.Path(path).parent)
	return projects

def is_cmake_project(path:pathlib.Path) -> bool:
	with open(path, "r") as build_file:
		for line in build_file.readlines():
			if re.match(r"^project(.*)$", line) is not None:
				return True
	return False
			

def find_cmake_projects(repo_path:pathlib.Path) -> list[pathlib.Path]:
	projects = []
	res = glob.glob("**/CMakeLists.txt", root_dir=repo_path, recursive=True)
	for path in res:
		if is_cmake_project(dir_to_search.joinpath(pathlib.Path(path))):
			projects.append(pathlib.Path(path).parent)
	return projects

repo_path = dir_to_search.resolve()
print(f"Scanning {repo_path}")
print() 
print("Finding STM32CubeMX projects...")
mx_projects = find_mx_projects(repo_path)
print(f"Found {len(mx_projects)} projects:")
mx_projects_resolved = {str(repo_path.joinpath(project_path).resolve()) for project_path in mx_projects}
for path in mx_projects:
	print(path) 

print()
print("Finding CMake projects...")
cmake_projects = find_cmake_projects(repo_path)
cmake_projects_resolved = {str(repo_path.joinpath(project_path).resolve()) for project_path in mx_projects}
cmake_projects_count = len(cmake_projects)
print(f"Found {cmake_projects_count} projects:")
for path in cmake_projects:
	print(path)

print()
print(f"Executing {cmake_projects_count} builds")
print()

successful_builds = 0
failed_builds = 0
is_lib = 0
failed = []

for project_path in cmake_projects:

	print()
	print("-"*75)
	print(f"Building {project_path}")
	print("-"*75)
	print()

	oci_runtime = "podman"
	if shutil.which("podman") is None:
		oci_runtime = "docker"
	command = [
		oci_runtime, "run", "--rm",
		"-v", f"{repo_path}:/home/ci-runner/project:z", container_image, 
		str(project_path)
	]
	if str(repo_path.joinpath(project_path).resolve()) in mx_projects_resolved:
		command.append("--stm32cubemx")
	else:
		is_lib+=1

	proc = subprocess.Popen(command)
	while proc.poll() is None:
		if proc.stdout is not None:
			print(proc.stdout)
		if proc.stderr is not None:
			print(proc.stderr)

	print()
	print(f"Exit code: {proc.returncode}")

	if proc.returncode == 0:
		print("Build Successful")
		successful_builds+=1
	else:
		print("Build Failed")
		failed_builds+=1
		failed.append(project_path)

print()
print("-"*75)
print("Summary:")
print("-"*75)
print(f"Libraries: {is_lib}")
print(f"Firmware: {cmake_projects_count-is_lib}")
print()
print(f"{successful_builds} succeeded")
print(f"{failed_builds} failed")


if failed_builds > 0:
	print("Failed build paths:")
	for project in failed:
		print(project)
	exit(1)