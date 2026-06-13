from importlib.metadata import version, PackageNotFoundError

from .client import IdaIpyClient, set_debug
from .result import Result

try:
    __version__ = version("idaipy")
except PackageNotFoundError:
    __version__ = "0.2.0"

__all__ = ["IdaIpyClient", "set_debug", "Result"]
