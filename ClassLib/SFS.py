import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib import *

class SFS_Csh_emb( Complex_Base ):
    def __init__( self, origin, params, trans_in=None ):
        self.params = params

        self.r_out = params[0]
        self.dr = params[1]
        self.r_in = self.r_out - self.dr
        self.n_semiwaves = params[2]
        self.s = params[3]
        self.alpha = params[4]
        self.r_curve = params[5]
        self.n_pts_cwave = params[6]
        self.Z1 = params[7]
        self.d_alpha1 = params[8]
        self.width1 = params[9]
        self.gap1 = params[10]
        self.Z2 = params[11]
        self.d_alpha2 = params[12]
        self.width2 = params[13]
        self.gap2 = params[14]
        self.n_pts_arcs = params[15]
        
        self.squid_params = self.params[16:]
        
        super( SFS_Csh_emb, self ).__init__( origin, trans_in )
        '''
        self.excitation_port = self.connections[0]
        self.output_port = self.connections[1]
        self.excitation_angle = self.angle_connections[0]
        self.output_angle = self.angle_connections[1]
        '''
        
    def init_primitives( self ):
        
        origin = DPoint(0,0)
        
        self.c_wave = CWave( origin, self.r_out, self.dr, self.n_semiwaves, self.s, self.alpha, self.r_curve, n_pts=self.n_pts_cwave )
        self.primitives["c_wave"] = self.c_wave
        
        Z1_start = origin + DPoint( 0, self.r_in+ self.gap1 + self.width1/2 )
        Z1_end = Z1_start + DPoint( 0, -self.gap1 - self.width1/2 + self.dr )
        self.cpw1 = CPW( self.Z1.width, self.Z1.gap, Z1_start, Z1_end )
        self.primitives["cpw1"] = self.cpw1
        
        Z2_start = origin - DPoint( 0, self.r_in + self.gap2 + self.width2/2 )
        Z2_end = Z2_start - DPoint( 0, -self.gap2 - self.width2/2 + self.dr )
        self.cpw2 = CPW( self.Z2.width, self.Z2.gap, Z2_start, Z2_end )        
        self.primitives["cpw2"] = self.cpw2
        
        self.c_wave_2_cpw_adapter = CWave2CPW( self.c_wave, self.params[7:15], n_pts=self.n_pts_arcs )
        self.primitives["c_wave_2_cpw_adapter"] = self.c_wave_2_cpw_adapter
        
        p_squid = None
        squid_trans_in = None
        
        if( self.c_wave.n_segments%2 == 1 ):
            squid_trans_in = DCplxTrans( 1, self.c_wave.alpha*180/pi, False, 0,0 )
            p_squid = origin
        else:
            squid_trans_in = None
            
            second_parity = self.c_wave.n_segments/2
            y_shift = self.c_wave.L0*sin(self.c_wave.alpha) - self.c_wave.r_curve*(1/cos(self.c_wave.alpha)-1)
            if( second_parity%2 == 0 ):
                p_squid = origin + DPoint( 0, y_shift )
            else:
                p_squid = origin + DPoint( 0, -y_shift )
        
        self.squid = Squid( p_squid, self.squid_params, trans_in=squid_trans_in )
        self.primitives["qubit"] = self.squid
       
        self.connections = [Z1_end, Z2_end]
        self.angle_connections = [pi/2, 3/2*pi]
        
    def place( self, dest, layer_ph=-1, layer_el=-1 ):
        for prim_name in list(self.primitives.keys())[:-1]:
            self.primitives[prim_name].place( dest, layer_ph )
        self.squid.place( dest, layer_el )