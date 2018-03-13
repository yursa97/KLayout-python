import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.Coplanars import *
from ClassLib.Shapes import *

class CWave2CPW( Element_Base ):
    '''
    Draws a semi-circle coupler from coplanar waveguide to jelly capacitance plates.


    '''
    def __init__( self, c_wave_cap, params, n_pts=50, trans_in=None ):
        self.c_wave_ref = c_wave_cap
        self.Z1 = params[0]
        self.d_alpha1 = params[1]
        self.width1 = params[2]
        self.gap1 = params[3]
        self.Z2 = params[4]
        self.d_alpha2 = params[5]
        self.width2 = params[6]
        self.gap2 = params[7]
        self.n_pts = n_pts
        super().__init__( self.c_wave_ref.origin, trans_in )

    def _get_solid_arc( self, center, R, width, alpha_start, alpha_end, n_inner, n_outer ):
        pts = []

        d_alpha_inner = (alpha_end - alpha_start)/(n_inner - 1)
        d_alpha_outer = -(alpha_end - alpha_start)/(n_outer-1)

        for i in range( 0,n_inner ):
            alpha = alpha_start + d_alpha_inner*i
            pts.append( center + DPoint( cos( alpha ), sin( alpha ) )*(R - width/2) )
        for i in range( 0,n_outer ):
            alpha = alpha_end + d_alpha_outer*i
            pts.append( center + DPoint( cos( alpha ), sin( alpha ) )*(R + width/2) )

        return DSimplePolygon( pts )

    def init_regions( self ):
        origin = DPoint(0,0)
        arc_1_solid = self._get_solid_arc( origin, self.c_wave_ref.in_circle.r + self.gap1 + self.width1/2, self.width1,
                                                    pi/2 - self.d_alpha1/2, pi/2 + self.d_alpha1/2,
                                                    self.n_pts,self.n_pts )
        arc_1_empty = self._get_solid_arc( origin, self.c_wave_ref.in_circle.r + self.gap1/2, self.gap1,
                                                    pi/2 - self.d_alpha1/2, pi/2 + self.d_alpha1/2,
                                                    self.n_pts,self.n_pts )

        arc_2_solid = self._get_solid_arc( origin, self.c_wave_ref.in_circle.r + self.gap2 + self.width2/2, self.width2,
                                                    3/2*pi - self.d_alpha2/2, 3/2*pi + self.d_alpha2/2,
                                                    self.n_pts,self.n_pts )
        arc_2_empty = self._get_solid_arc( origin, self.c_wave_ref.in_circle.r + self.gap2/2, self.gap2,
                                                    3/2*pi - self.d_alpha2/2, 3/2*pi + self.d_alpha2/2,
                                                    self.n_pts,self.n_pts )
        self.metal_region.insert( arc_1_solid )
        self.metal_region.insert( arc_2_solid )
        self.empty_region.insert( arc_1_empty )
        self.empty_region.insert( arc_2_empty )

class CWave( Complex_Base ):
    '''
    Draws a condensator from a circle cutting it into 2 pieces.

    Parameters:
        center: DPoint
            A center of circle.
        r_out: float
            The outer radius of a circle (along to the edge of the ground).
        dr: float
            The gap in between the common ground and the circle perimeter.
        n_segments: int
            The number of segments (without turns) composed into a condensator gap.
        s: float
            The half-width of the gap.
        alpha: rad
            The angle of single arc of slice.
        r_curve: float
            The radius of single arc.
        n_pts: int
            The number of points on the perimeter of the circle.
        solid: ???
        L0: float
            The length of the initial and final "RLR" sections of the slice.
        trans_in: Bool
            Initial transformation

    '''

    def __init__(self, center, r_out, dr, n_segments, s, alpha, r_curve, n_pts=50, solid=True, trans_in=None ):
        self.r_out = r_out
        self.dr = dr
        self.n_segments = n_segments
        self.s = s
        self.alpha = alpha
        self.r_curve = r_curve
        self.n_pts = n_pts
        self.delta = 40e3
        self.L_full = 2*self.r_out - 2*self.delta
        # calculating parameters of the CPW_RL_Path #
        r = self.r_curve
        n = self.n_segments
        L_full = self.L_full
        alpha = self.alpha
        if abs(self.alpha) != pi:
            self.L1 = L_full/((n_segments+1)*cos(alpha))
            self.L0 = self.L1/2
            r = self.r_curve
        else:
            raise ValueError("180 degrees turns in CWave are not supported.")

        if( self.L0 < 0 or self.L1 < 0 ):
            print( "CPW_RL_Path: impossible parameters combination" )

        super(). __init__( center,trans_in )

    def init_primitives(self):
        origin = DPoint(0,0)
        #erased line params
        Z = CPWParameters( 0, self.s/2 )
        shapes = ''
        angles = []
        lengths = []
        # placing circle r_out with dr clearance from ground polygon
        self.empt_circle = Circle( origin,self.r_out + self.dr, n_pts=self.n_pts, solid=False )
        self.in_circle = Circle( origin, self.r_out, n_pts=self.n_pts, solid=True )
        self.empt_circle.empty_region -= self.in_circle.metal_region
        self.primitives["empt_circle"] = self.empt_circle
        self.primitives["in_circle"] = self.in_circle

        self.RL_start = origin + DPoint( -self.in_circle.r,0 )
        shapes += 'LRL'
        angles.extend([self.alpha])
        lengths.extend([self.delta, self.L0])
        #rl_path_start = CPW_RL_Path(self.RL_start, "LRLR", Z, self.r_curve, [self.delta, self.L0], [self.alpha,-self.alpha] )
        #self.primitives["rl_start"] = rl_path_start

        # intermidiate RLRs
        for i in range(self.n_segments):
            if( i%2 == 1 ):
                m_x = -1
            else:
                m_x = 1
            shapes += 'RL'
            angles.extend([-2*m_x*self.alpha])
            lengths.extend([self.L1])
            # prev_path = list(self.primitives.values())[-1]
            # rl_path_p = CPW_RL_Path( prev_path.end, "RLR", Z, self.r_curve, [self.L1], [-m_x*self.alpha,m_x*self.alpha])
            # self.primitives["rl_path_" + str(i)] = rl_path_p
            # ending RLR
        if( self.n_segments%2 == 1 ):
            m_x = 1
        else:
            m_x = -1
        shapes += 'RLRL'
        angles.extend([2*m_x*self.alpha,-m_x*self.alpha])
        lengths.extend([self.L0, self.delta])

        cut = CPW_RL_Path(self.RL_start,shapes,Z,self.r_curve,lengths,angles)
        # prev_path = list(self.primitives.values())[-1]
        # rl_path_end = CPW_RL_Path( prev_path.end, "RLRL", Z, self.r_curve, [self.L0, self.delta], [m_x*self.alpha,-m_x*self.alpha])
        self.primitives["cut"] = cut
