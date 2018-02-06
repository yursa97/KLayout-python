import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.Coplanars import *
from ClassLib.Shapes import *

class CWave2CPW( Element_Base ):
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
        super( CWave2CPW, self ).__init__( self.c_wave_ref.origin, trans_in )
    
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
    def __init__(self, center, r_out, dr, n_semiwaves, s, alpha, r_curve, n_pts=50,solid=True, L0=None, trans_in=None ):
        self.r_out = r_out
        self.dr = dr
        self.n_semiwaves = n_semiwaves
        self.s = s
        self.alpha = alpha
        self.r_curve = r_curve
        self.n_pts = n_pts
        
        ## MAGIC VARIABLE ##
        self.delta = 2e3 # 2 mkm from each side of circle will be erased along the diameter
        
        self.L_x = 2*self.r_out - 2*self.delta
        # calculating parameters of the CPW_RL_Path #
        L_x = self.L_x
        r = self.r_curve
        n = self.n_semiwaves
        alpha = self.alpha
        if( self.alpha == pi/2 or self.alpha == -pi/2 ):
            self.L0 = L0
            self.r_curve = L_x/(2*n+2)
            r = self.r_curve
        else:
            self.L0 = ( ( L_x + 2*(n-1)*r*tan(alpha/2) ) / ( 2*n ) - 2*r*sin(alpha) ) / cos(alpha)
        self.L1 = 2*r*tan(alpha/2) + 2*self.L0
        if( self.L0 < 0 or self.L1 < 0 ):
            print( "CPW_RL_Path: impossible parameters combination" )
        
        super( CWave,self ). __init__( center,trans_in )
            
    def init_primitives(self):
        origin = DPoint(0,0)
        #erased line params
        Z = CPW( 0, self.s/2 )
        
        # placing circle r_out with dr clearance from ground polygon
        self.empt_circle = Circle( origin,self.r_out + self.dr, n_pts=self.n_pts, solid=False )
        self.in_circle = Circle( origin, self.r_out, n_pts=self.n_pts, solid=True )
        self.empt_circle.empty_region -= self.in_circle.metal_region
        self.primitives["empt_circle"] = self.empt_circle
        self.primitives["in_circle"] = self.in_circle
        
        # pads on left and right sides        
        left = DPoint( -self.r_out, 0 )
        self.pad_left = CPW( Z.width, Z.gap, left, left + DPoint( self.delta, 0 ) )
        self.primitives["pad_left"] = self.pad_left
        
        right = DPoint( self.r_out,0 )
        self.pad_right = CPW( Z.width, Z.gap, right, right + DPoint( -self.delta,0 ) )
        self.primitives["pad_right"] = self.pad_right
        
        # starting RLR
        self.RL_start = origin + DPoint( -self.in_circle.r + self.delta,0 )
        rl_path_start = CPW_RL_Path( self.RL_start, "RLR", [Z], [self.r_curve], [self.L0], [self.alpha,-self.alpha] )
        self.primitives["rl_start"] = rl_path_start
        
        # ending RLR
        if( self.n_semiwaves%2 == 0 ):
            m_x = False
        else:
            m_x = True
        self.RL_end = origin + DPoint( self.in_circle.r - self.delta,0 )
        rl_path_end = CPW_RL_Path( self.RL_end, "RLR", [Z], [self.r_curve], [self.L0], [self.alpha,-self.alpha], trans_in = DCplxTrans( 1,180, m_x, 0,0 ) )

        
        # intermidiate RLRs
        for i in range(self.n_semiwaves - 1):
            if( i%2 == 0 ):
                m_x = False
            else:
                m_x = True 
                
            prev_path = list(self.primitives.values())[-1]
            rl_path_p = CPW_RL_Path( prev_path.end, "RLR", [Z], [self.r_curve], [self.L1], [-self.alpha,self.alpha], trans_in=DCplxTrans( 1,0,m_x,0,0 ) )
            self.primitives["rl_path_" + str(i)] = rl_path_p
        
        self.primitives["rl_path_end"] = rl_path_end