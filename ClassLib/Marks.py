import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import Complex_Base
from ClassLib.Shapes import Cross
from ClassLib.Coplanars import CPW_arc

class Shamil_mark( Complex_Base ):
    def __init__(self,origin,trans_in=None):
        self.cross_in_a = 20e3
        self.cross_out_a = 40e3
        if( self.cross_out_a < self.cross_in_a ):
            print( "cross inner square must be larger than outer" )
        super( Shamil_mark, self ).__init__( origin, trans_in )
        
    def init_primitives( self ):
        origin = DPoint( 0,0 )
        self.primitives["cross"] = Cross( origin, self.cross_in_a, self.cross_out_a )
        
        Z = CPWParamters( 10e3,0 )
        self.primitives["left_arc"] = CPW_arc( Z, 
        