#!/usr/bin/env python
"""
打包腳本 - 自動化打包流程

依賴安裝：
    pip install -r requirements-dev.txt

使用方式：
    python scripts/pack.py                    # 基本打包
    python scripts/pack.py --version 1.0.0    # 指定版本號
"""

import argparse
import shutil
import sys
from pathlib import Path
from subprocess import check_call


def run(cmd: list[str]) -> int:
    print(">>", " ".join(cmd))
    return check_call(cmd, shell=True)


def clean_build():
    """清理舊的打包文件"""
    print("=" * 50)
    print("清理舊的打包文件")
    print("=" * 50)

    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["VERSION"]

    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"清理 {dir_name}/ ...")
            shutil.rmtree(dir_path)

    for pattern in files_to_clean:
        for file_path in Path(".").glob(pattern):
            print(f"刪除 {file_path} ...")
            file_path.unlink()

    return True


def generate_version(version=None):
    """生成 VERSION 文件"""
    print("=" * 50)
    print("生成 VERSION 文件")
    print("=" * 50)

    cmd = [sys.executable, "scripts/generate_version.py"]
    if version:
        cmd.extend(["--version", version])

    result = run(cmd)
    if result != 0:
        print("❌ 生成 VERSION 文件失敗")
        return False

    return True


def check():
    """檢查代碼"""
    print("=" * 50)
    print("檢查代碼")
    print("=" * 50)

    result = run([sys.executable, "scripts/check.py"])
    if result != 0:
        print(
            "❌ 代碼檢查未通過，請先修復問題，透過 `python scripts/check.py --fix` 嘗試自動修復"
        )
        return False

    return True


def pack_exe():
    """使用 PyInstaller 打包"""
    print("=" * 50)
    print("使用 PyInstaller 打包")
    print("=" * 50)

    result = run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "StarResonanceFishing.spec",
        ]
    )
    if result != 0:
        print("❌ 打包失敗")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="自動化打包腳本")
    parser.add_argument("--version", help="指定版本號")
    args = parser.parse_args()

    try:
        # 清理舊的打包文件
        if not clean_build():
            sys.exit(1)

        # 生成版本
        if not generate_version(args.version):
            sys.exit(1)

        # 代碼檢查
        if not check():
            sys.exit(1)

        # 打包
        if not pack_exe():
            sys.exit(1)

        # 打包成功
        print("=" * 50)
        print("✓ 打包成功！")
        print("=" * 50)
        print(
            f"輸出文件: {Path('dist').absolute() / 'StarResonanceFishing.exe'}"
        )

    except KeyboardInterrupt:
        print("\n\n用戶中斷打包")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 打包過程發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
