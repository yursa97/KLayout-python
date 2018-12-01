import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon,DPolygon,Polygon, Region,DPath,DVector
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib._PROG_SETTINGS import *
from ClassLib.BaseClasses import Element_Base

class Rectangle( Element_Base ):
    def __init__( self, origin, a,b, trans_in=None, inverse=False ):
        self.a = a
        self.b = b
        super( Rectangle,self ).__init__( origin, trans_in, inverse )
        
    def init_regions( self ):
        origin = DPoint(0,0)
        p1 = origin + DPoint(self.a,0)
        p2 = p1 + DPoint(0,self.b)
        p3 = p2 + DPoint(-self.a,0)
        pts_arr = [origin,p1,p2,p3]
        self.metal_region.insert( SimplePolygon().from_dpoly( DSimplePolygon(pts_arr) ) )

class Cross( Element_Base ):
    def __init__( self, origin, inner_square_a, outer_square_a, trans_in=None ):
        self.in_a = inner_square_a
        self.out_a = outer_square_a
        self.center = origin + DPoint( self.out_a/2, self.out_a/2 )
        super( Cross, self ).__init__( origin, trans_in )
        self.center = self.connections[0]
        
    def init_regions( self ):
        origin = DPoint(0,0)
        w = self.out_a/2 - self.in_a/2
        
        rec1 = Rectangle( origin, w,w )
        p2 = origin + DPoint(self.in_a + w,0)
        rec2 = Rectangle( p2, w,w )
        p3 = origin + DPoint( self.in_a+w,self.in_a+w )
        rec3 = Rectangle( p3, w, w )
        p4 = origin + DPoint( 0, self.in_a + w )
        rec4 = Rectangle( p4, w, w )
        
        tmp_reg = Region()
        
        rec1.place( tmp_reg )
        rec2.place( tmp_reg )
        rec3.place( tmp_reg )
        rec4.place( tmp_reg )
        
        rec = Rectangle( origin, self.out_a, self.out_a )
        rec.place( self.metal_region )
        
        self.empty_region = tmp_reg
        self.connections = [self.center]

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
