import glob
import json
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

if len(sys.argv) < 2:
	print("No directory to scan was provided")
	sys.exit(1)
if len(sys.argv) < 3:
	print("No runner container image was provided")
	sys.exit(1)

dir_to_search = pathlib.Path(sys.argv[1].strip())
oci_runtime = sys.argv[2]
container_image = sys.argv[3]
denylist_file = None
process_submodules = False
if len(sys.argv) == 5:
	denylist_file = sys.argv[4]
if len(sys.argv) == 6 and sys.argv[5] == "--process-submodules":
	process_submodules = True

def get_submodules(current_dir:Path|str) -> list[Path]:
	if shutil.which("git") is not None:
		process_repo_path = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,check=False, text=True, cwd=current_dir)
		if process_repo_path.returncode != 0:
			print("Could not get repo path", file=sys.stderr)
			print("Git Output:", file=sys.stderr)
			print(process_repo_path.stderr, file=sys.stderr)
		else:
			repo_path = pathlib.Path(process_repo_path.stdout.strip()).resolve()
			process = subprocess.run(["git", "submodule", "status", str(current_dir)], capture_output=True,check=False, text=True, cwd=repo_path)
			if process.returncode != 0:
				print("Could not get submodules", file=sys.stderr)
				print("Git Output:", file=sys.stderr)
				print(process.stderr, file=sys.stderr)
			else:
				submodule_paths = []
				data = process.stdout
				lines = data.splitlines()
				for line in lines:
					relative_path = shlex.split(line)[1]
					absolute_path = repo_path.joinpath(pathlib.Path(relative_path))
					submodule_paths.append(absolute_path)
				return submodule_paths
	else:
		print("Could not get submodules, git was not found", file=sys.stderr)
	return []

def read_denylist(file_path:str|None) -> set[Path]:
	if file_path is None:
		return set()
	denylist_file_path = Path(file_path)
	if denylist_file_path.exists():
		with open(file_path, "r") as denylist_file_handle:
			data = json.load(denylist_file_handle)
			denylisted_paths = set()
			if "paths" in data:
				for entry in data["paths"]:
					if type(entry) is not str:
						print(f"Bad entry of type {type(entry)} was found: {entry}", file=sys.stderr)
					else:
						denylisted_paths.add(pathlib.Path(entry).resolve())
				return denylisted_paths
			else:
				print("Bad blocklist file, skipping denylist", file=sys.stderr)
	else:
		print("Blocklist file does not exist, skipping denylist", file=sys.stderr)
	return set()

def find_mx_projects(repo_path:pathlib.Path, denylist:set[Path]) -> list[pathlib.Path]:
	projects = []
	res = glob.glob("**/**.ioc", root_dir=repo_path, recursive=True)
	for path in res:
		file_path = pathlib.Path(path)
		for denylisted in denylist:
			# denylisted always resolved before
			# join to repo_path to resolve correctly
			if denylisted in repo_path.joinpath(file_path).resolve().parents:
				break
		else:
			projects.append(file_path.parent)
	return projects

def is_cmake_project(path:pathlib.Path) -> bool:
	with open(path, "r") as build_file:
		for line in build_file:
			if re.match(r"^project(.*)$", line) is not None:
				return True
	return False
			

def find_cmake_projects(repo_path:pathlib.Path, denylist:set[Path]) -> list[pathlib.Path]:
	projects = []
	res = glob.glob("**/CMakeLists.txt", root_dir=repo_path, recursive=True)
	for path in res:
		file_path = pathlib.Path(path)
		if is_cmake_project(dir_to_search.joinpath(file_path)):
			for denylisted in denylist:
				# denylisted always resolved before
				# join to repo_path to resolve correctly
				if denylisted in repo_path.joinpath(file_path).resolve().parents:
					break
			else:
				projects.append(file_path.parent)
	return projects

denylist = read_denylist(denylist_file)
repo_path = dir_to_search.resolve()
print(f"Scanning {repo_path}")
submodules = get_submodules(repo_path)
denylist.update(submodules)
print(f"Detected {len(denylist)} directories to skip")
print() 
print("Finding STM32CubeMX projects...")
mx_projects = find_mx_projects(repo_path, denylist)
print(f"Found {len(mx_projects)} projects:")
mx_projects_resolved = {str(repo_path.joinpath(project_path).resolve()) for project_path in mx_projects}
for path in mx_projects:
	print(path) 

print()
print("Finding CMake projects...")
cmake_projects = find_cmake_projects(repo_path, denylist)
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
	sys.exit(1)