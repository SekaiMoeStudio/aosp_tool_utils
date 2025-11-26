#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from collections import defaultdict
from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError


def find_files(paths, recursive=False):
    """Find all files in given paths (non-recursive by default)."""
    file_paths = []
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Warning: Path does not exist: {path}")
            continue
        if path.is_file():
            file_paths.append(path)
        elif path.is_dir():
            if recursive:
                file_paths.extend(path.rglob("*"))
            else:
                file_paths.extend(path.iterdir())
    return [p for p in file_paths if p.is_file()]


def get_dependencies(so_files):
    """
    For each .so file, extract its needed shared libraries.
    Returns: {filename: [list_of_deps]}
    """
    deps_map = {}
    for so_path in so_files:
        try:
            with open(so_path, "rb") as f:
                elf = ELFFile(f)
                # Only consider shared objects
                if elf.header.e_type != "ET_DYN":
                    continue

                deps = []
                for segment in elf.iter_segments():
                    if segment.header.p_type == "PT_DYNAMIC":
                        for tag in segment.iter_tags():
                            if tag.entry.d_tag == "DT_NEEDED":
                                deps.append(tag.needed)
                deps_map[so_path.name] = deps
        except (ELFError, OSError) as e:
            print(f"Warning: Could not read or parse ELF file {so_path}: {e}")
            continue
    return deps_map


def identify_missing(blobs_to_deps):
    """
    Find dependencies that are not present as blobs in the input set.
    Returns: {missing_lib: [list_of_blobs_needing_it]}
    """
    # Build reverse map: dependency -> [blobs that need it]
    dep_to_blobs = defaultdict(list)
    for blob, deps in blobs_to_deps.items():
        for dep in deps:
            dep_to_blobs[dep].append(blob)

    # Find missing deps: those not present as a blob filename
    available_blobs = set(blobs_to_deps.keys())
    missing = {}
    for dep, blobs in dep_to_blobs.items():
        if dep not in available_blobs:
            missing[dep] = blobs
    return missing


def display_missing(missing_blobs):
    for dep, blobs in missing_blobs.items():
        print(f"{dep} required by: {'; '.join(blobs)}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Find missing .so dependencies in a set of shared libraries."
    )
    parser.add_argument("PATHS", nargs="+", help="Paths to .so files or directories containing them")
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search paths recursively"
    )
    args = parser.parse_args()

    all_files = find_files(args.PATHS, recursive=args.recursive)
    so_files = [f for f in all_files if f.suffix == ".so"]

    if not so_files:
        print("No .so files found.")
        return

    blobs_to_deps = get_dependencies(so_files)
    missing = identify_missing(blobs_to_deps)
    display_missing(missing)


if __name__ == "__main__":
    main()
