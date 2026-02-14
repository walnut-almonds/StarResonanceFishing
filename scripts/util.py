#!/usr/bin/env python
"""Project utility functions."""

import subprocess
import sys


def run(cmd: list[str]):
    print(">>", " ".join(cmd))
    subprocess.run(args=cmd, check=True)


def abort(*values: object):
    """打印錯誤訊息並退出"""
    print(*values, file=sys.stderr)
    sys.exit(1)
