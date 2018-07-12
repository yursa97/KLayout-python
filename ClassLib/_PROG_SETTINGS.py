import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

class PROGRAM:
    LAYER1_NUM = 7
    LAYER2_NUM = 8  
  
class CHIP:
    dx = 10.1e6
    dy = 5.1e6
    L1 = 2466721
    gap = 150e3
    width = 260e3
    b = 2*gap + width
    origin = DPoint( 0,0 )
    box = pya.DBox( origin, origin + DPoint( dx,dy ) )
    # only 4 connections programmed by now
    connections = [box.p1 + DPoint( L1 + b/2,0 ), box.p1 + DPoint( dx - (L1+b/2),0 ), box.p2 - DPoint( L1 + b/2,0 ),  box.p1 + DPoint( L1 + b/2, dy )]

class Chip5x10_with_contactPads( Complex_Base ):
    '''
    This object is implementing chip surface with 
    some default contact pads that are already present
    '''
    
    def __init__( self, origin, Z_params, trans_in=None ):
        '''
        @params:
            origin: DPoint
                position of the left-buttom corner of the chip
            Z_params: Coplanars.CPWParameters class instance
                parameters of the coplanar waveguide used as inner end of the
                contact pads.
        '''
        self.chip_x = 10e6
        self.chip_y = 5e6
        self.Z_params = Z_params
        super( Chip5x10_with_contactPads, self ).__init__( origin, trans_in )
        
    def init_primitives( self ):
        origin = DPoint(0,0)
        
        # drawing chip        
        self.chip = Rectangle( origin, self.chip_x, self.chip_y )
        self.primitives["chip"] = self.chip

        # contact pads
        self.contact_pad_left = Contact_Pad( origin + DPoint(0,self.chip_y/2),{"w":self.Z_params.width,"g":Z_params.gap} )
        self.primitives["cp_left"] = self.contact_pad_left
        
        self.contact_pad_right = Contact_Pad( origin + DPoint(self.chip_x,self.chip_y/2),{"w":self.Z_params.width,"g":Z_params.gap},
                                                                    trans_in = Trans.R180 )
        self.primitives["cp_right"] = self.contact_pad_right
        
        # top and bottom pads
        N_pads = 3
        self.connections = [self.contact_pad_left.end,self.contact_pad_right.end]
        self.angle_connections = [self.contact_pad_left.angle_connections[1], self.contact_pad_right.angle_connections[1]]
        
        self.contact_pads_top = [Contact_Pad( origin + DPoint(self.chip_x/(N_pads+1)*(i+1),self.chip_y),{"w":self.Z_params.width,"g":Z_params.gap},
                                                                    trans_in = Trans.R270 ) for i in range(0,N_pads)]
        for i in range(0,N_pads):
            self.primitives["cp_top_" + str(i)] = self.contact_pads_top[i]
            self.connections.append( self.contact_pads_top[i].end )
            self.angle_connections.append( self.contact_pads_top[i].angle_connections[1] )
            
        self.contact_pads_bottom = [Contact_Pad( origin + DPoint(self.chip_x/(N_pads+1)*(i+1),0),{"w":self.Z_params.width,"g":Z_params.gap},
                                                                    trans_in = Trans.R90 ) for i in range(0,N_pads)]
        for i in range(0,N_pads):
            self.primitives["cp_bot_" + str(i)] = self.contact_pads_bottom[i]
            self.connections.append( self.contact_pads_bottom[i].end )
            self.angle_connections.append( self.contact_pads_bottom[i].angle_connections[1] ) 

       
        

            
            








