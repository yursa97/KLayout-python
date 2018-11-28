import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,DPath,DVector,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib._PROG_SETTINGS import *
from ClassLib.BaseClasses import Element_Base

class Circle( Element_Base ):
    def __init__(self,center,r,trans_in=None,n_pts=50,solid=True, offset_angle=0):
        self.center = center
        self._offset_angle = offset_angle
        self.r = r
        self.n_pts = n_pts
        self.solid = solid
        super(). __init__( center,trans_in )

    def init_regions(self):
        dpts_arr = [DPoint(self.r*cos(2*pi*i/self.n_pts+self._offset_angle),self.r*sin(2*pi*i/self.n_pts+self._offset_angle)) for i in range(0,self.n_pts)]
        if( self.solid == True ):
            self.metal_region.insert( SimplePolygon().from_dpoly( DSimplePolygon(dpts_arr) ) )
        else:
            self.empty_region.insert( SimplePolygon().from_dpoly( DSimplePolygon(dpts_arr) ) )
        self.connections.extend([self.center, self.center + DVector(0,-self.r)])
        self.angle_connections.extend([0, 0])

class Kolbaska(Element_Base):
    def __init__(self, origin, stop, width, r, trans_in=None):
        self._width = width
        self._vec = stop - origin
        self._r = r
        super().__init__(origin, trans_in)

    def init_regions(self):
        ext_start = self._r
        ext_end = self._r
        shps = [self._width, ext_start, ext_end]
        kolb = DPath([DPoint(), DPoint() + self._vec],*shps,True)
        self.metal_region.insert(kolb)
        self.connections.extend([DPoint(0,0), DPoint() + self._vec])
        self.angle_connections.extend([0, 0])

class Circle_arc( Element_Base ):
    def __init__( self, center, r, alpha_start=0, alpha_end = pi, trans_in=None, n_pts=50, solid=True ):
        self.center = center
        self.r = r
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.n_pts = n_pts
        self.solid = solid
        super( Circle_arc,self ). __init__( center,trans_in )

    def init_regions( self ):
        d_alpha = (self.alpha_end - self.alpha_start)/(self.n_pts - 1)
        alphas = [(self.alpha_start + d_alpha*i) for i in range(0,self.n_pts)]
        dpts_arr = [DPoint(self.r*cos(alpha),self.r*sin(alpha)) for alpha in alphas]
        dpts_arr.append( DPoint(0,0) )

        if( self.solid == True ):
            self.metal_region.insert( SimplePolygon().from_dpoly( DSimplePolygon(dpts_arr) ) )
        else:
            self.empty_region.insert( SimplePolygon().from_dpoly( DSimplePolygon(dpts_arr) ) )
        self.connections.extend([self._center, self._center+DVector(0, -self.r)])
        self.angle_connections.extend([0,0])
