import argparse
import os
import subprocess


def validate_file(file_path: str) -> str:
    """Check if the provided file exists and is readable."""
    if not os.path.isfile(file_path):
        raise argparse.ArgumentTypeError(f"File '{file_path}' does not exist.")
    if not os.access(file_path, os.R_OK):
        raise argparse.ArgumentTypeError(f"File '{file_path}' is not readable.")
    return file_path


def post_proc_module(dir: str, module: str) -> str:
    ROOT_PATTERN = "@"
    if module.startswith(ROOT_PATTERN):
        # This is a qualified module name
        # so dont add the "dir" before it
        return module[len(ROOT_PATTERN) :].replace(".", "/") + ".cml"
    return os.path.join(dir, module.replace(".", "/")) + ".cml"


def get_direct_deps(file_path: str) -> list[str]:
    # NOTE: We only allow imports on the first line for now
    try:
        with open(file_path, "r") as file:
            # Gather file meta-data
            dir = os.path.dirname(file_path)
            # get the deps out
            first_line = file.readline().strip()
            PRE_LINE = "(* deps: "
            POST_LINE = " *)"
            if first_line.startswith(PRE_LINE) and first_line.endswith(POST_LINE):
                module_snip = first_line[len(PRE_LINE) : -(len(POST_LINE))].strip()
                modules = module_snip.split(" ")
                return list(map(lambda mod: post_proc_module(dir, mod), modules))
            else:
                # No 'open' statement found
                return []
    except FileNotFoundError:
        raise ValueError(f"File '{file_path}' does not exist")


def get_trans_deps(file_path: str, seen: list[str]) -> list[str]:
    deps = get_direct_deps(file_path)
    full_deps = []
    for dep in deps:
        if dep not in seen:
            new_deps = get_trans_deps(dep, seen + [dep] + full_deps)
            full_deps.extend(new_deps)
    return full_deps + [file_path]


def print_mode(args, deps):
    if args.out:
        with open(args.out, "w") as outfile:
            outfile.write("\n".join(deps))
    else:
        print(deps)


def merge_mode(args, deps):
    if not args.out:
        raise ValueError("Output file name (--out <file>) is required in 'build' mode.")
    # We presume if someone specifies an output file, they are fine with it being written over
    # Build a monolithic CakeML file
    with open(args.out, "w") as outfile:
        for dep in deps:
            with open(dep, "r") as infile:
                outfile.write(infile.read())
                outfile.write("\n\n")
    return args.out


def build_mode(args, deps):
    CC = "gcc"
    BASIS_FILE = "basis_ffi.c"
    CC_FLAGS = "-O2 -lm"
    # first we build the monolithic file via merge_mode
    out_file = merge_mode(args, deps)
    # then we build the binary

    # Generate assembly file from the monolithic CakeML file
    asm_file = out_file.replace(".cml", ".S")
    binary_file = out_file.replace(".cml", "")
    try:
        subprocess.run(f"cake < {out_file} > {asm_file}", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during CakeML compilation: {e}")

    # Compile the assembly file into a binary using GCC
    try:
        subprocess.run(
            f"{CC} {BASIS_FILE} {asm_file} {CC_FLAGS} -o {binary_file}",
            shell=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during GCC compilation: {e}")

    print(f"Binary created: {binary_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate dependencies for a CakeML project."
    )
    parser.add_argument(
        "main",
        type=validate_file,
        help="Main CakeML file with the final 'main' function in it.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["print", "merge", "build"],
        required=True,
        default="print",
        help="Mode of operation: 'print' to print dependencies, 'merge' to build a monolithic CakeML file for the project, and 'build' to build a monolithic CakeML file and then create a binary out of it.",
    )
    parser.add_argument(
        "--out",
        type=str,
        help="Output file name for the monolithic CakeML file.",
    )

    args = parser.parse_args()

    deps = get_trans_deps(args.main, [])

    match args.mode:
        case "print":
            print_mode(args, deps)
        case "merge":
            merge_mode(args, deps)
        case "build":
            build_mode(args, deps)
        case _:
            raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
