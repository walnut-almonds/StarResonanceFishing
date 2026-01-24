"""
釣魚自動化模組
"""

from importlib.metadata import PackageNotFoundError, version

__version__ = "unknown"

try:
    __version__ = version("star-resonance-fishing")
except PackageNotFoundError:
    # package is not installed
    pass
