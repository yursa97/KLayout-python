from importlib import reload

from . import matlabClient
reload(matlabClient)

from . import sonnetLab
reload(sonnetLab)
from .sonnetLab import SonnetLab