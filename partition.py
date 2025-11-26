#!/usr/bin/env python3

# usage: python3 main.py vendor

import argparse
import subprocess
import sys
import re


def run_adb_shell(cmd: str) -> str:
    """Run an adb shell command and return stripped stdout, or empty string on error."""
    try:
        result = subprocess.run(
            ["adb", "shell", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def get_block_device_name(partition_name: str) -> str:
    """Get the actual block device name (e.g., 'sda12') from a by-name symlink."""
    cmd = f"ls -la /dev/block/bootdevice/by-name/{partition_name} 2>/dev/null"
    output = run_adb_shell(cmd)
    if not output:
        return ""

    # Example line: lrwxrwxrwx 1 root root 20 2024-01-01 00:00 system -> /dev/block/sda12
    # We want to extract 'sda12'
    if " -> /dev/block/" in output:
        # Split by " -> /dev/block/" and take the part after
        parts = output.split(" -> /dev/block/")
        if len(parts) > 1:
            block_name = parts[1].strip()
            # In case it's still a full path like 'mmcblk0p12', take basename
            return block_name.split("/")[-1]
    return ""


def get_partition_size_bytes(block_name: str) -> int:
    """Read /proc/partitions and return size in bytes for the given block name."""
    output = run_adb_shell("cat /proc/partitions")
    if not output:
        return -1

    lines = output.splitlines()
    for line in lines:
        parts = line.split()
        if len(parts) >= 4 and parts[3] == block_name:
            try:
                size_in_blocks = int(parts[2])  # size in 1K blocks
                return size_in_blocks * 1024    # convert to bytes
            except ValueError:
                continue
    return -1


def main():
    parser = argparse.ArgumentParser(
        description="Get the size (in bytes) of an Android partition by its by-name label."
    )
    parser.add_argument("partition", nargs="?", help="Partition name (e.g., system, vendor)")
    args = parser.parse_args()

    if not args.partition:
        print(f"Usage: {sys.argv[0]} [partition name]")
        sys.exit(1)

    partition_name = args.partition.strip()
    block_name = get_block_device_name(partition_name)

    if not block_name:
        print(f"Error: partition {partition_name} not found")
        sys.exit(1)

    size_bytes = get_partition_size_bytes(block_name)
    if size_bytes < 0:
        print(f"Error: could not determine size for block device '{block_name}'")
        sys.exit(1)

    print(size_bytes)


if __name__ == "__main__":
    main()
