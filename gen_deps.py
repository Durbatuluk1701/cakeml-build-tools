"""
Overall steps:
1. we take in a file for "main" file
2. read the file and get its imports
3. for each import, we check if it is a local file or a library
"""

import argparse
import sys
import os


def validate_file(file_path: str) -> str:
    """Check if the provided file exists and is readable."""
    if not os.path.isfile(file_path):
        raise argparse.ArgumentTypeError(f"File '{file_path}' does not exist.")
    if not os.access(file_path, os.R_OK):
        raise argparse.ArgumentTypeError(f"File '{file_path}' is not readable.")
    return file_path


def post_proc_module(module: str) -> str:
    return module.replace(".", "/") + ".cml"


def get_modules(file_path: str) -> list[str]:
    """Read the file and extract 'open' statements."""
    # NOTE: We only allow imports on the first line for now
    try:
        with open(file_path, "r") as file:
            first_line = file.readline().strip()
            if first_line.startswith("(* open ") and first_line.endswith(" *)"):
                first_line = first_line[8:-3].strip()
                modules = first_line.split(" ")
                return list(map(post_proc_module, modules))
            else:
                # No 'open' statement found
                return []
    except FileNotFoundError:
        raise ValueError(f"File '{file_path}' does not exist")


def main():
    parser = argparse.ArgumentParser(
        description="Generate dependencies for a CakeML project."
    )
    parser.add_argument(
        "--main",
        type=validate_file,
        required=True,
        help="Main CakeML file with the final 'main' function in it.",
    )

    args = parser.parse_args()

    proc_list: list[str] = [args.main]
    deps = {}
    while proc_list:
        current_file = proc_list.pop(0)
        modules = get_modules(current_file)
        deps[current_file] = modules
        for module in modules:
            if module not in deps.keys() and module not in proc_list:
                proc_list.append(module)
    # Print the dependencies
    for file, deps_list in deps.items():
        print(f"{file}: {', '.join(deps_list)}")


if __name__ == "__main__":
    main()
