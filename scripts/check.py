#!/usr/bin/env python
"""Project check.

依賴安裝：
    pip install -r requirements-dev.txt

使用方式：
    python scripts/check.py       # 只檢查不修復
    python scripts/check.py --fix # 自動修復問題，並檢查
"""

import argparse
import subprocess
import sys


def run(cmd: list[str]):
    print(">>", " ".join(cmd))
    subprocess.run(args=cmd, check=True)


def abort(*values: object):
    """打印錯誤訊息並退出"""
    print(*values, file=sys.stderr)
    sys.exit(1)


def main():
    try:
        parser = argparse.ArgumentParser(description="執行代碼檢查工具")
        parser.add_argument("--fix", action="store_true", help="執行修復操作")
        args = parser.parse_args()

        # Prepare command sequence
        if args.fix:
            cmds = [
                [sys.executable, "-m", "ruff", "format"],
                [sys.executable, "-m", "ruff", "check", "--fix"],
                [sys.executable, "-m", "ty", "check"],  # 沒有修復模式。
            ]
        else:
            cmds = [
                [sys.executable, "-m", "ruff", "format", "--check"],
                [sys.executable, "-m", "ruff", "check"],
                [sys.executable, "-m", "ty", "check"],
            ]

        for cmd in cmds:
            run(cmd)

        print("\n代碼檢查通過")

    except Exception as e:
        abort(f"\n代碼檢查發生錯誤: {e}")


if __name__ == "__main__":
    main()
