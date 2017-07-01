VERBOSITY = [9]

__version__ = "0.1.1-git"
__author__ = "Vitaly Potyarkin"
__all__ = [
    "WebUI",
    "debug",
    "settings",
    "VERBOSITY"
]

from hlc.web import WebUI, debug
from hlc.cfg import settings
