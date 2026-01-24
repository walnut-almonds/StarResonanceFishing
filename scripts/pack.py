#!/usr/bin/env python
"""
打包腳本 - 自動化打包流程

依賴安裝：
    pip install -r requirements-dev.txt

使用方式：
    python scripts/pack.py                    # 基本打包
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]):
    print(">>", " ".join(cmd))
    subprocess.run(args=cmd, check=True)


def abort(*values: object):
    """打印錯誤訊息並退出"""
    print(*values, file=sys.stderr)
    sys.exit(1)


def clean():
    """清理舊的打包文件"""
    print("=" * 50)
    print("清理舊的打包文件")
    print("=" * 50)

    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = []

    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"清理 {dir_name}/ ...")
            shutil.rmtree(dir_path)

    for pattern in files_to_clean:
        for file_path in Path(".").glob(pattern):
            print(f"刪除 {file_path} ...")
            file_path.unlink()


def check():
    """檢查代碼"""
    print("=" * 50)
    print("檢查代碼")
    print("=" * 50)

    run([sys.executable, "scripts/check.py"])


def pack():
    """使用 PyInstaller 打包"""
    print("=" * 50)
    print("使用 PyInstaller 打包")
    print("=" * 50)

    run([sys.executable, "-m", "PyInstaller", "StarResonanceFishing.spec"])


def main():
    try:
        clean()  # 清理舊的打包文件

        check()  # 代碼檢查

        pack()  # 打包

        # 打包成功
        print("=" * 50)
        print("✓ 打包成功！")
        print("=" * 50)
        print(
            f"輸出文件: {Path('dist').absolute() / 'StarResonanceFishing.exe'}"
        )

    except KeyboardInterrupt:
        abort("\n用戶中斷打包")

    except Exception as e:
        abort(f"\n打包過程發生錯誤: {e}")


if __name__ == "__main__":
    main()
