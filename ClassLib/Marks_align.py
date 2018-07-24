import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import Complex_Base

class Shamil_mark( Complex_Base ):
    def __init__(self,origin,trans_in=None):
        self.square_a = 20e3
        super( Shamil_mark, self ).__init__( origin, trans_in )
        
    def init_primitives( self ):
        pass
        