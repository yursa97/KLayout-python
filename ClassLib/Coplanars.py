import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import *

class CPW( Element_Base ):
    """@brief: class represents single coplanar waveguide
      @params:   float width - represents width of the central conductor
                        float gap - spacing between central conductor and ground planes
                        float gndWidth - width of ground plane to be drawed 
                        DPoint start - center aligned point, determines the start point of the coplanar segment
                        DPoint end - center aligned point, determines the end point of the coplanar segment
    """
    def __init__(self, width, gap, start=DPoint(0,0), end=DPoint(0,0), gndWidth=-1, trans_in=None ):                    
        self.width = width
        self.gap = gap
        self.b = 2*gap + width
        self.gndWidth = gndWidth
        self.end = end
        self.start = start
        self.dr = end - start
        super( CPW, self ).__init__( start, trans_in )
        self.start = self.connections[0]
        self.end = self.connections[1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]
        
    def init_regions( self ):
        self.connections = [DPoint(0,0),self.dr]
        self.start = DPoint(0,0)
        self.end = self.start + self.dr
        alpha = atan2( self.dr.y, self.dr.x )
        self.angle_connections = [alpha,alpha]
        alpha_trans = ICplxTrans().from_dtrans( DCplxTrans( 1,alpha*180/pi,False, self.start ) )
        self.metal_region.insert( pya.Box( Point().from_dpoint(DPoint(0,-self.width/2)), Point().from_dpoint(DPoint( self.dr.abs(), self.width/2 )) ) )
        self.empty_region.insert( pya.Box( Point().from_dpoint(DPoint(0,self.width/2)), Point().from_dpoint(DPoint( self.dr.abs(), self.width/2 + self.gap )) ) )
        self.empty_region.insert( pya.Box( Point().from_dpoint(DPoint(0,-self.width/2-self.gap)), Point().from_dpoint(DPoint( self.dr.abs(), -self.width/2 )) ) )
        self.metal_region.transform( alpha_trans )
        self.empty_region.transform( alpha_trans )


class CPW_arc( Element_Base ):
    def __init__(self, Z0, start, R, delta_alpha, gndWidth = -1, trans_in=None ):
        self.R = R
        self.start = start
        self.center = start + DPoint( 0,self.R )
        self.end = self.center + DPoint( sin(delta_alpha), -cos(delta_alpha) )*self.R
        self.dr = self.end - self.start
        
        self.width = Z0.width
        self.gap = Z0.gap
        
        self.delta_alpha = delta_alpha
        self.alpha_start = 0
        self.alpha_end = self.delta_alpha

        super( CPW_arc,self ).__init__( start, trans_in )
        self.start = self.connections[0]
        self.end = self.connections[1]
        self.center = self.connections[2]
        
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

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
        self.connections = [DPoint(0,0),self.dr,DPoint(0,self.R)]
        self.angle_connections = [self.alpha_start,self.alpha_end]
        self.start = DPoint(0,0)
        self.end = self.dr
        self.center = DPoint(0,self.R)
        n_inner = 200
        n_outer = 200
        metal_arc = self._get_solid_arc( self.center, self.R, self.width, self.alpha_start - pi/2, self.alpha_end - pi/2, n_inner, n_outer )  
        self.metal_region.insert( SimplePolygon().from_dpoly( metal_arc ) )
        empty_arc1 = self._get_solid_arc( self.center, self.R - (self.width + self.gap)/2, self.gap, self.alpha_start - pi/2, self.alpha_end - pi/2, n_inner, n_outer )  
        self.empty_region.insert( SimplePolygon().from_dpoly( empty_arc1 ) )
        empty_arc2 = self._get_solid_arc( self.center, self.R + (self.width + self.gap)/2, self.gap, self.alpha_start - pi/2, self.alpha_end - pi/2, n_inner, n_outer )  
        self.empty_region.insert( SimplePolygon().from_dpoly( empty_arc2 ) )
        
        
class CPW2CPW( Element_Base ):
    def __init__( self, Z0, Z1, start, end, trans_in=None ):
        self.Z0 = Z0
        self.Z1 = Z1
        self.start = start
        self.end = end
        self.dr = self.end - self.start
        super( CPW2CPW,self ).__init__( start, trans_in )
        self.start = self.connections[0]
        self.end = self.connections[1]
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]
        
    def init_regions( self ):
        self.connections = [DPoint(0,0),DPoint(self.dr.abs(),0)]
        self.angle_connections = [0,0]
        alpha = atan2( self.dr.y, self.dr.x )
        self.angle_connections = [alpha,alpha]
        alpha_trans = DCplxTrans( 1,alpha*180/pi,False, 0,0 )
        m_poly = DSimplePolygon( [DPoint(0,-self.Z0.width/2), DPoint(self.dr.abs(),-self.Z1.width/2), DPoint(self.dr.abs(),self.Z1.width/2), DPoint(0,self.Z0.width/2)] )
        e_poly1 = DSimplePolygon( [DPoint(0,-self.Z0.b/2), DPoint(self.dr.abs(),-self.Z1.b/2), DPoint(self.dr.abs(),-self.Z1.width/2), DPoint(0,-self.Z0.width/2)] )
        e_poly2 = DSimplePolygon( [DPoint(0,self.Z0.b/2), DPoint(self.dr.abs(),self.Z1.b/2), DPoint(self.dr.abs(),self.Z1.width/2), DPoint(0,self.Z0.width/2)] )
        m_poly.transform( alpha_trans )
        e_poly1.transform( alpha_trans )
        e_poly2.transform( alpha_trans )
        self.metal_region.insert( SimplePolygon.from_dpoly(m_poly) )
        self.empty_region.insert( SimplePolygon.from_dpoly(e_poly1) )
        self.empty_region.insert( SimplePolygon.from_dpoly(e_poly2) )
  
class Path_RSRS( Complex_Base ):
    def __init__( self, Z0, start, L1, L2, R1, R2, trans_in=None ):
        self.Z0 = Z0
        self.L1 = L1
        self.L2 = L2
        self.R1 = R1
        self.R2 = R2
        super( Path_RSRS,self ).__init__( start, trans_in )
        self.start = self.connections[0]
        self.end = self.connections[1]
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]
        
        
    def init_primitives( self ):
        self.arc1 = CPW_arc( self.Z0, DPoint(0,0), self.R1, pi/4 )
        self.cop1 = CPW( self.Z0.width, self.Z0.gap, self.arc1.end, self.arc1.end + DPoint( sin(pi/4), sin(pi/4) )*self.L1 )
        self.arc2 = CPW_arc( self.Z0, self.cop1.end, self.R2, pi/4, trans_in=DCplxTrans( 1,45,False,0,0 ) )
        self.cop2 = CPW( self.Z0.width, self.Z0.gap,  self.arc2.end, self.arc2.end + DPoint( 0,self.L2 ) )
        
        self.connections = [self.arc1.start,self.cop2.end]
        self.angle_connections = [self.arc1.alpha_start, self.cop2.alpha_end]
        
        self.primitives = {"arc1":self.arc1, "cop1":self.cop1, "arc2":self.arc2, "cop2":self.cop2}
        
class Path_RS(Complex_Base):
    def __init__(self, Z0, start, end, trans_in=None):
        self.Z0 = Z0
        self.end = end
        self.dr = end - start
        super(Path_RS, self).__init__(start, trans_in)
        self.start = self.connections[0]
        self.end = self.connections[1]
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

    def init_primitives(self):
        L = abs(abs(self.dr.y) - abs(self.dr.x))
        r = min(abs(self.dr.y), abs(self.dr.x))
        if(abs(self.dr.y) > abs(self.dr.x)):
            self.arc1 = CPW_arc(self.Z0, DPoint(0, 0), copysign(
                r, self.dr.y), copysign(pi/2, self.dr.x*self.dr.y))
            self.cop1 = CPW(self.Z0.width, self.Z0.gap, self.arc1.end,
                            self.arc1.end + DPoint(0, copysign(L, self.dr.y)))
            self.connections = [self.arc1.start, self.cop1.end]
            self.angle_connections = [self.arc1.alpha_start, self.cop1.alpha_end]
        else:
            self.cop1 = CPW(self.Z0.width, self.Z0.gap, DPoint(
                0, 0), DPoint(0, 0) + DPoint(copysign(L, self.dr.x), 0))
            self.arc1 = CPW_arc(self.Z0, self.cop1.end, copysign(
                r, self.dr.y), copysign(pi/2, self.dr.y*self.dr.x))
            self.connections = [ self.cop1.start, self.arc1.end]
            self.angle_connections = [ self.cop1.alpha_start,self.arc1.alpha_end]
            
        self.primitives = {"arc1": self.arc1, "cop1": self.cop1}

        
class Coil_type_1( Complex_Base ):
    def __init__( self, Z0, start, L1, r, L2, trans_in=None ):
        self.Z0 = Z0
        self.L1 = L1
        self.r = r
        self.L2 = L2
        super( Coil_type_1,self ).__init__( start, trans_in )
        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]
        
    def init_primitives( self ):
            self.cop1 = CPW( self.Z0.width, self.Z0.gap, DPoint(0,0), DPoint( self.L1,0 ) )
            self.arc1 = CPW_arc( self.Z0, self.cop1.end, -self.r, -pi )
            self.cop2 = CPW( self.Z0.width, self.Z0.gap, self.arc1.end, self.arc1.end - DPoint( self.L2,0 ) )
            self.arc2 = CPW_arc( self.Z0, self.cop2.end, -self.r, pi )
            
            self.connections = [self.cop1.start,self.arc2.end]
            self.angle_connections = [self.cop1.alpha_start,self.arc2.alpha_end]
            self.primitives = {"cop1":self.cop1,"arc1":self.arc1,"cop2":self.cop2,"arc2":self.arc2}
            
            
from collections import Counter

class CPW_RL_Path( Complex_Base ):
    def __init__( self, start, RL_str, Z_list, R_list, L_list, delta_alpha_list, trans_in = None ):
        self.RL_str = RL_str
        self.N_elements = len(RL_str)
        self.RL_counter = Counter( RL_str )
        
        # periodically filling  Z,R,L lists to make their length equal to the RL_str
        self.Z_list = [Z_list[i%len(Z_list)] for i in range( self.N_elements )]
        self.R_list = [R_list[i%len(R_list)] for i in range( self.RL_counter['R'] )]
        self.L_list = [L_list[i%len(L_list)] for i in range( self.RL_counter['L'] )]
        self.delta_alpha_list = delta_alpha_list
        
        super( CPW_RL_Path, self ).__init__( start, trans_in )
        self.start = self.connections[0]
        self.end = self.connections[1]
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]
        
    def init_primitives( self ):
        R_index = 0
        L_index = 0
        origin = DPoint(0,0)
        # placing the first element
        symbol_0 = self.RL_str[0]
        if( symbol_0 == 'R' ):
            if( self.delta_alpha_list[0] > 0 ):
                sgn = 1
            else:
                sgn = -1
                    
            R = self.R_list[R_index]*sgn
            delta_alpha = self.delta_alpha_list[R_index]       
            self.primitives["arc_0"] = CPW_arc( self.Z_list[0],origin, R,delta_alpha )
            R_index += 1
        elif( symbol_0 == 'L' ):
            self.primitives["cpw_0"] = CPW( self.Z_list[0].width, self.Z_list[0].gap, self.start, self.start + DPoint( self.L_list[0],0 ) )
            L_index += 1
        
        for i,symbol in enumerate(self.RL_str):
            if( i == 0 ):
                continue

            prev_primitive = list(self.primitives.values())[i-1]     
                       
            if( symbol == 'R' ):
                if( self.delta_alpha_list[R_index] > 0 ):
                    sgn = 1
                else:
                    sgn = -1
                    
                R = self.R_list[R_index]*sgn
                delta_alpha = self.delta_alpha_list[R_index]
            
                cpw_arc = CPW_arc( self.Z_list[i],prev_primitive.end, R, delta_alpha, 
                                                    trans_in=DCplxTrans(1,prev_primitive.alpha_end*180/pi, False,0,0) )
                self.primitives["arc_"+str(R_index)] = cpw_arc
                R_index += 1
                
            elif( symbol == 'L' ):
                cpw = CPW( self.Z_list[i].width, self.Z_list[i].gap,
                                        prev_primitive.end, prev_primitive.end + DPoint(self.L_list[L_index],0),
                                        trans_in=DCplxTrans(1,prev_primitive.alpha_end*180/pi,False,0,0) )
                self.primitives["cpw_"+str(L_index)] = cpw
                L_index += 1 
                
            self.connections = [origin, list(self.primitives.values())[-1].end]
            self.angle_connections = [0, list(self.primitives.values())[-1].alpha_end]