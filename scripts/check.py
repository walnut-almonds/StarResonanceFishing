#!/usr/bin/env python
"""Project check.

依賴安裝：
    pip install -r requirements-dev.txt

使用方式：
    python scripts/check.py       # 只檢查不修復
    python scripts/check.py --fix # 自動修復問題，並檢查
"""

import argparse
import sys
from subprocess import check_call


def run(cmd: list[str]) -> int:
    print(">>", " ".join(cmd))
    return check_call(cmd, shell=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="執行代碼檢查工具",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="執行修復操作",
    )
    args = parser.parse_args()

    # Prepare command sequence
    if args.fix:
        cmds: list[list[str]] = [
            [sys.executable, "-m", "ruff", "format", "."],
            [sys.executable, "-m", "ruff", "check", ".", "--fix"],
            [sys.executable, "-m", "ty", "check"],  # 沒有修復模式。
        ]
    else:
        cmds = [
            [sys.executable, "-m", "ruff", "format", "--check", "."],
            [sys.executable, "-m", "ruff", "check", "."],
            [sys.executable, "-m", "ty", "check"],
        ]

    # Run commands sequentially; fail fast on any non-zero exit code
    for cmd in cmds:
        rc = run(cmd)
        if rc != 0:
            print(f"❌ command '{' '.join(cmd)}' failed with code {rc}")
            return rc

    print("\n✅ All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
