import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region, DBox, Box
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans, DPath, SaveLayoutOptions, Shape
from importlib import reload
#reload(ClassLib)
import ClassLib
from ClassLib import *
reload(ClassLib)
from ClassLib import *
from ClassLib.Shapes import Circle

# Enter your Python code here
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

class StickQubit_Cap(Element_Base):

    def __init__(self, origin, s_w, s_l, gap_w, gap_l, trans_in=None):
        self._s_w = s_w
        self._s_l = s_l
        self._gap_w = gap_w
        self._gap_l = gap_l
        super().__init__(origin, trans_in)

    def init_regions(self):
        ll = DPoint(-self._s_l/2, -self._s_w/2)
        ur = DPoint(self._s_l/2, self._s_w/2)
        self.metal_region.insert(Box(DBox(ll,ur)))
        ll = DPoint(-(self._s_l+self._gap_l)/2, -(self._s_w+self._gap_w)/2)
        ur = DPoint((self._s_l+self._gap_l)/2, (self._s_w+self._gap_w)/2)
        protect_reg = Region(Box(DBox(ll,ur)))
        empty_region = protect_reg - self.metal_region
        self.empty_region.insert(empty_region)
        self.connections = [DPoint(0,0)]

        
class CHIP:
    dx = 0.8e6
    dy = 0.8e6
chip_center = DPoint(CHIP.dx/2, CHIP.dy/2)
        
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
    layer_photo = layout.layer( info )
    layer_el = layout.layer( info2 )

    # clear this cell and layer
    #cell.clear()

    # setting layout view
    lv.select_cell(cell.cell_index(), 0)
    lv.add_missing_layers()

    ### DRAW SECTION START ###
    origin = DPoint(0,0)
    # Chip drwaing START #
    chip = pya.DBox(DPoint(-CHIP.dx/2, -CHIP.dy/2),DPoint(CHIP.dx/2, CHIP.dy/2))
    cell.shapes(layer_photo).insert(pya.Box(chip))
    # Chip drawing END #

    # Single photon source photo layer drawing START #
    Z_top = CPWParameters(10e3, 5e3) # sizes of a connected CPW (central conductor width, gap)
    Z_bottom = CPWParameters(20e3,10e3) # some reluctant CPW
    r_out = 175e3 # Radius of an outer ring including the empty region
    r_gap = 25e3 # Gap in the outer ring
    n_segments = 2
    s = 10e3 # Gap between two pads of a central capacitor
    alpha = pi/4 # period of a gap zigzag
    r_curve = 30e3 # curvature of the roundings at the edges of a zigzag
    n_pts_cwave = 200

    Z1 = Z_top # Parameters of a top CPW
    d_alpha1 = 0 # width of a tip of a central conductor of the top CPW
    width1 = 0 # width of a conductor in the bottom semiring
    gap1 = r_gap - 1.33e3 # gap between the bottom semiring and the central capacitor
    Z2 = Z_bottom # Paramters of a bottom CPW
    d_alpha2 = 1/3*pi # length of a circumference covered by the bottom semiring
    width2 = r_gap/3
    gap2 = width2
    n_pts_arcs = 50
    params = [r_out, r_gap, n_segments, s, alpha, r_curve, n_pts_cwave,
                  Z1, d_alpha1, width1, gap1, Z2, d_alpha2, width2, gap2 , n_pts_arcs]
                  
    pad_side = 5e3
    pad_r = 1e3
    pads_distance = 30e3
    p_ext_width = 3e3
    p_ext_r = 0.5e3
    sq_len = 7e3
    sq_area = 15e6
    j_width = 0.4e3
    low_lead_w = 0.5e3
    b_ext =   0.9e3
    j_length =  0.3e3
    n = 7
    bridge = 0.5e3

    pars_squid = [pad_side,pad_r,pads_distance,p_ext_width,\
                  p_ext_r,sq_len,sq_area,j_width,low_lead_w,\
                  b_ext,j_length,n,bridge]
                  
    p = DPoint( 0, 0 )
    sfs = SFS_Csh_emb( p, params + pars_squid )
    sfs.place( cell, layer_photo, layer_el )
    # Single photon source photo layer drawing END #

    # CPW leading to edges
    feedline = CPW(Z1.width, Z1.gap, DPoint(0, CHIP.dy/2), sfs.connections[0])
    outline = CPW(Z2.width, Z2.gap, DPoint(0, -CHIP.dy/2), sfs.connections[1])
    
    feedline.place(cell,layer_photo)
    #outline.place(cell,layer_photo)  

    lv.zoom_fit()
