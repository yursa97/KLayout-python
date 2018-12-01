import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import *

class Line_N_JJCross( Element_Base ):
    def __init__( self, origin, params, trans_in=None  ):
        self.params = params
        self.a = params[0]
        self.b = params[1]
        self.jos1_b = params[2]
        self.jos1_a = params[3]
        self.f1 = params[4]
        self.d1 = params[5]
        self.jos2_b = params[6]
        self.jos2_a = params[7]
        self.f2 = params[8]
        self.d2 = params[9]
        self.w = params[10]
        
        self.poly1 = self._make_polygon( self.b, self.w, self.d1, self.f1,   self.d2 )
        
        super( Line_N_JJ,self ).__init__( origin, trans_in )  
        
    def _make_polygon( self, length, w, d, f, overlapping ):
        polygon = DSimplePolygon
        p1 = DPoint(0,0)
        p2 = p1 + DPoint( length,0 )
        p3 = p2 + DPoint( 0, w )
        p4 = p3 - DPoint( overlapping,0 )
        p5 = p4 - DPoint( 0, d )
        p6 = p5 - DPoint( f,0 )
        p7 = p6 + DPoint( 0, d )
        p8 = p1 + DPoint( 0,w )
        
        polygon = DSimplePolygon( [p1,p2,p3,p4,p5,p6,p7,p8] )
        return polygon
        
    def init_regions( self ):
        self.metal_region.insert( SimplePolygon().from_dpoly( self.poly1 ) )