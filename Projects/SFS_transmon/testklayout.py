import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DPath
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
import ClassLib
reload(ClassLib)
from ClassLib import *

import sonnetSim
reload(sonnetSim)
from sonnetSim import SonnetLab

class ResonatorSimulator(Chip_Design):

    origin = DPoint(0, 0)

    # Call other methods drawing parts of the design from here
    def draw(self):
        self.draw_path()
    
    def drawPath(self):
        DPath()


### MAIN FUNCTION ###
if __name__ == "__main__":
    tester = Tester('tester')
    tester.show()