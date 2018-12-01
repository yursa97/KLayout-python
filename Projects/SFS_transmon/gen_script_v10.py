<<<<<<< HEAD
import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
from ClassLib import *
reload(ClassLib)
from ClassLib import *

### START classes to /be delegated to different file ###
class SFS_Csh_emb( Complex_Base ):
    def __init__( self, origin, params, trans_in=None ):
        self.params = params
        self.r_out = params[0]
        self.dr = params[1]
        self.n_semiwaves = params[2]
        self.s = params[3]
        self.alpha = params[4]
        self.r_curve = params[5]
        self.n_pts_cwave = params[6]
        self.L0 = params[7]
        self.delta = params[8]
        self.Z1 = params[9]
        self.d_alpha1 = params[10]
        self.width1 = params[11]
        self.gap1 = params[12]
        self.Z2 = params[13]
        self.d_alpha2 = params[14]
        self.width2 = params[15]
        self.gap2 = params[16]
        self.n_pts_arcs = params[17]
        super( SFS_Csh_emb, self ).__init__( origin, trans_in )
        
        self.excitation = self.connections[0]
        self.output = self.connections[1]
        self.excitation_angle = self.angle_connections[0]
        self.output_angle = self.angle_connections[1]
        
        
    def init_primitives( self ):
        origin = DPoint(0,0)
        
        self.c_wave = CWave( origin, self.r_out, self.dr, self.n_semiwaves, self.s, self.alpha, self.r_curve, n_pts=self.n_pts_cwave, L0=self.L0, delta=self.delta )
        self.primitives["c_wave"] = self.c_wave
        
        Z1_start = origin + DPoint( 0,self.r_out + self.gap1 + self.width1/2 )
        Z1_end = Z1_start + DPoint( 0, -self.gap1 - self.width1/2 + self.dr )
        self.cpw1 = CPW( self.Z1.width, self.Z1.gap, Z1_start, Z1_end )
        self.primitives["cpw1"] = self.cpw1
        
        Z2_start = origin - DPoint( 0,self.r_out + self.gap1 + self.width1/2 )
        Z2_end = Z2_start - DPoint( 0, -self.gap1 - self.width1/2 + self.dr )
        self.cpw2 = CPW( self.Z2.width, self.Z2.gap, Z2_start, Z2_end )        
        self.primitives["cpw2"] = self.cpw2
        
        self.c_wave_2_cpw_adapter = CWave2CPW( self.c_wave, self.params[9:17], n_pts=self.n_pts_arcs )
        self.primitives["c_wave_2_cpw_adapter"] = self.c_wave_2_cpw_adapter
       
        self.connections = [Z1_end, Z2_end]
        self.angle_connections = [pi/2, 3/2*pi]    
        
        
    
# END classes to be delegated to different file ###

# Enter your Python code here
### MAIN FUNCTION ###
if __name__ == "__main__":
# getting main references of the application
    app = pya.Application.instance()
    mw = app.main_window()
    lv = mw.current_view()
    cv = None
    
    #this insures that lv and cv are valid objects
    if( lv == None ):
        cv = mw.create_layout(1)
        lv = mw.current_view()
    else:
        cv = lv.active_cellview()

# find or create the desired by programmer cell and layer
    layout = cv.layout()
    layout.dbu = 0.001
    if( layout.has_cell( "testScript") ):
        pass
    else:
        cell = layout.create_cell( "testScript" )
    
    info = pya.LayerInfo(1,0)
    info2 = pya.LayerInfo(2,0)
    layer_ph = layout.layer( info )
    layer_el = layout.layer( info2 )

    # clear this cell and layer
    cell.clear()

    # setting layout view  
    lv.select_cell(cell.cell_index(), 0)
    lv.add_missing_layers()

    ### DRAW SECTION START ###
    origin = DPoint(0,0)
    
    # Chip drwaing START #
    Z_params = CPWParameters( 14.5e3, 6.7e3 ) 
    chip = Chip5x10_with_contactPads( origin, Z_params )
    chip.place( cell, layer_ph )
    # Chip drawing END #
    
    width = 300e3
    gap = 200e3
    Z = CPW( width,gap, DPoint(0,chip.chip_y/2), DPoint(chip.chip_x,chip.chip_y/2) )
    Z.place( cell, layer_ph )
    
    from SonnetLab import *
    
    lv.zoom_fit()
    
    writer = Matlab_commander()
    print("starting connection...")
    writer.send( CMD.SAY_HELLO )
    writer.send( CMD.CLEAR_POLYGONS )
    writer.send_boxProps( chip.chip_x,chip.chip_y, 200,400 )
    poly_for_matlab = []
    reg = Region(cell.begin_shapes_rec( layer_ph ))
    for polygon in reg:
        print( polygon.to_simple_polygon().points )
        
    writer.send_polygon( [0,0,100,100],[45,55,55,45], [1,3] )
    writer.send_set_ABS_sweep( 1, 10 )
    writer.send( CMD.SIMULATE )
    file_name = writer.read_line().decode("ASCII")
    print("visualizing...")
    writer.send( CMD.VISUALIZE )
    print("closing connection" )
    writer.send( CMD.CLOSE_CONNECTION )
    print("connection closed\n")
    writer.close()
=======
import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
from ClassLib import *

### START classes to be delegated to different file ###
                
class SFS_Csh_emb( Complex_Base ):
    def __init__( self, origin, params, trans_in=None ):
        self.params = params
        self.r_out = params[0]
        self.dr = params[1]
        self.n_semiwaves = params[2]
        self.s = params[3]
        self.alpha = params[4]
        self.r_curve = params[5]
        self.n_pts_cwave = params[6]
        self.L0 = params[7]
        self.Z1 = params[8]
        self.d_alpha1 = params[9]
        self.width1 = params[10]
        self.gap1 = params[11]
        self.Z2 = params[12]
        self.d_alpha2 = params[13]
        self.width2 = params[14]
        self.gap2 = params[15]
        self.n_pts_arcs = params[16]
        super( SFS_Csh_emb, self ).__init__( origin, trans_in )
        '''
        self.excitation_port = self.connections[0]
        self.output_port = self.connections[1]
        self.excitation_angle = self.angle_connections[0]
        self.output_angle = self.angle_connections[1]
        '''
        
    def init_primitives( self ):
        origin = DPoint(0,0)
        
        self.c_wave = CWave( origin, self.r_out, self.dr, self.n_semiwaves, self.s, self.alpha, self.r_curve, n_pts=self.n_pts_cwave, L0=self.L0 )
        self.primitives["c_wave"] = self.c_wave
        
        Z1_start = origin + DPoint( 0,self.r_out + self.gap1 + self.width1/2 )
        Z1_end = Z1_start + DPoint( 0, -self.gap1 - self.width1/2 + self.dr )
        self.cpw1 = CPW( self.Z1.width, self.Z1.gap, Z1_start, Z1_end )
        self.primitives["cpw1"] = self.cpw1
        
        Z2_start = origin - DPoint( 0,self.r_out + self.gap1 + self.width1/2 )
        Z2_end = Z2_start - DPoint( 0, -self.gap1 - self.width1/2 + self.dr )
        self.cpw2 = CPW( self.Z2.width, self.Z2.gap, Z2_start, Z2_end )        
        self.primitives["cpw2"] = self.cpw2
        
        self.c_wave_2_cpw_adapter = CWave2CPW( self.c_wave, self.params[8:16], n_pts=self.n_pts_arcs )
        self.primitives["c_wave_2_cpw_adapter"] = self.c_wave_2_cpw_adapter
       

        
        self.connections = [Z1_end, Z2_end]
        self.angle_connections = [pi/2, 3/2*pi]
        
        
        
        
    
# END classes to be delegated to different file ###

# Enter your Python code here
### MAIN FUNCTION ###
if __name__ == "__main__":
# getting main references of the application
    app = pya.Application.instance()
    mw = app.main_window()
    lv = mw.current_view()
    cv = None
    
    #this insures that lv and cv are valid objects
    if( lv == None ):
        cv = mw.create_layout(1)
        lv = mw.current_view()
    else:
        cv = lv.active_cellview()

# find or create the desired by programmer cell and layer
    layout = cv.layout()
    layout.dbu = 0.001
    if( layout.has_cell( "testScript") ):
        pass
    else:
        cell = layout.create_cell( "testScript" )
    
    info = pya.LayerInfo(1,0)
    info2 = pya.LayerInfo(2,0)
    layer_ph = layout.layer( info )
    layer_el = layout.layer( info2 )

    # clear this cell and layer
    cell.clear()

    # setting layout view  
    lv.select_cell(cell.cell_index(), 0)
    lv.add_missing_layers()

    ### DRAW SECTION START ###
    origin = DPoint(0,0)
    
    # Chip drwaing START #    
    chip = pya.DBox( origin, DPoint( CHIP.dx, CHIP.dy ) )
    cell.shapes( layer_ph ).insert( pya.Box().from_dbox(chip) )
    # Chip drawing END #
    
    
    # Single photon source photo layer drawing START #
    r_out = 200e3
    r_gap = 25e3
    n_semiwaves = 4
    s = 5e3  
    alpha = pi/3
    r_curve = 2e4
    n_pts_cwave = 50
    L0 = 20e3
    
    Z = CPW( 14.5e3, 6.7e3 )
    Z1 = Z
    d_alpha1 = pi/3
    width1 = r_gap/3 
    gap1 = width1
    Z2 = Z
    d_alpha2 = 2/3*pi
    width2 = width1
    gap2 = width2
    n_pts_arcs = 50
    params = [r_out, r_gap,n_semiwaves, s, alpha, r_curve, n_pts_cwave, L0,
                        Z1,d_alpha1,width1,gap1,Z2,d_alpha2,width2,gap2, n_pts_arcs]
    p = DPoint( CHIP.dx/2, CHIP.dy/2 )
    sfs = SFS_Csh_emb( p, params )
    sfs.place(cell, layer_ph)
    # Single photon source photo layer drawing START #
    
    ### DRAW SECTION END ###
    
    lv.zoom_fit()
>>>>>>> dev_1
