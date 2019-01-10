print("invoking __init__.py from sonnetSim package")
from importlib import reload

from . import sonnetLab
reload(sonnetLab)
from .sonnetLab import SonnetLab