from ._ import *

import sys
if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    # Needs importlib-metadata backport installed for < 3.8
    import importlib_metadata as metadata

try:
    __version__ = metadata.version("oy3o") # 包名应与 pyproject.toml 一致
except metadata.PackageNotFoundError:
    __version__ = "unknown" # 或者其他默认值