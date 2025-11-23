#!/usr/bin/env python3
import sys
import re

def read_lines(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.rstrip('\n') for line in f]

def is_path_line(line):
    stripped = line.strip()
    return stripped and not stripped.startswith('#')

def extract_path_key(line):
    if not is_path_line(line):
        return None
    # 处理 src:dst
    if ':' in line:
        return line.split(':', 1)[0].strip()
    return line.strip()

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate_a_b.py <old_proprietary.txt> <new_proprietary.txt>", file=sys.stderr)
        sys.exit(1)

    old_file = sys.argv[1]
    new_file = sys.argv[2]

    old_lines = read_lines(old_file)
    new_lines = read_lines(new_file)

    # 构建 new 的路径集合（用于快速判断是否存活）
    new_path_set = set()
    for line in new_lines:
        key = extract_path_key(line)
        if key:
            new_path_set.add(key)

    # 构建 new 的完整行集合（用于 b.txt）
    new_line_set = set(new_lines)

    # 生成 a.txt: old 中未被删除的行（路径在 new 中存在，或非路径行）
    a_lines = []
    for line in old_lines:
        if not is_path_line(line):
            # 注释或空行，保留
            a_lines.append(line)
        else:
            key = extract_path_key(line)
            if key in new_path_set:
                a_lines.append(line)
            # 否则：路径被删除，跳过

    # 生成 b.txt: old 中完全逐行存在于 new 中的行
    b_lines = []
    for line in old_lines:
        if line in new_line_set:
            b_lines.append(line)

    # 写入 a.txt
    with open('a.txt', 'w') as f:
        for line in a_lines:
            f.write(line + '\n')

    # 写入 b.txt
    with open('b.txt', 'w') as f:
        for line in b_lines:
            f.write(line + '\n')

    print("✅ Generated from old and new files:")
    print(f"  a.txt -> {len(a_lines)} lines (unchanged or survived paths + all comments)")
    print(f"  b.txt -> {len(b_lines)} lines (lines that appear identically in both old and new)")
    print("\nNote:")
    print("  - a.txt keeps comments even if new file has different comments (as long as path exists)")
    print("  - b.txt only keeps lines that are byte-for-byte identical in both files")

if __name__ == '__main__':
    main()
