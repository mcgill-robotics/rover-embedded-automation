import pathlib
import sys


def convert_to_python_import(path:pathlib.Path):
    return ".".join(list(path.parts)).removesuffix(".py")

def main():
    if len(sys.argv) < 3:
        print("Not enough arguments")
        sys.exit(1)
    package_dir = sys.argv[1]
    output_file = sys.argv[2]
    package_path = pathlib.Path(package_dir)
    project_file = package_path.joinpath("pyproject.toml")
    if not project_file.exists():
        print("Not a project", file=sys.stderr)
        sys.exit(1)
    package_files = package_path.joinpath("src")
    with open(output_file, "w") as out:
        for path in package_files.glob("**/*.py"):
            relative_path = path.relative_to(package_files)
            if relative_path.stem != "__init__":
                py_import_path = convert_to_python_import(relative_path)
                out.write(f"import {py_import_path}\n")

        


if __name__ == "__main__":
    main()
