#!/usr/bin/env python
"""
生成 VERSION 文件的腳本
用於 CI/CD 打包時自動生成版本號

使用方式：
    python scripts/generate_version.py
    python scripts/generate_version.py --version 1.2.3
"""

import argparse
import subprocess
from pathlib import Path


def get_git_version():
    """從 git 獲取版本號"""
    try:
        # 嘗試獲取最新的 git tag
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()
        return tag
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        # 如果沒有 tag，使用 commit hash
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()
        return f"dev-{commit_hash}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "0.0.0"


def main():
    parser = argparse.ArgumentParser(description="生成 VERSION 文件")
    parser.add_argument(
        "--version", help="指定版本號（如不指定則從 git 自動獲取）"
    )
    args = parser.parse_args()

    # 獲取版本號
    if args.version:
        version = args.version
    else:
        version = get_git_version()

    # 移除可能的 'v' 前綴
    version = version.lstrip("v")

    # 寫入 VERSION 文件（放在工作目錄）
    version_file = Path.cwd() / "VERSION"
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(version)

    print(f"✓ VERSION 文件已生成: {version}")


if __name__ == "__main__":
    main()
