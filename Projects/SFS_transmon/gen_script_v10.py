import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
from ClassLib import *

### START classes to be delegated to different file ###
                

        
    
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
    
    # Coplanar parameters definition section
    Z = CPWParameters(20e3, 10e3)
    Zl = CPWParameters(10e3,7e3)
    cpw_curve = 40e3
    
    # Chip drwaing START #    
    chip = Chip5x10_with_contactPads( origin, Z  )
    chip.place( cell, layer_ph )
    # Chip drawing END #
    
    # Single photon source drawing START #
    p1 = chip.connections[0]
    p2 = chip.connections[2]
    

    r_out = 175e3 # Radius of an outer ring including the empty region
    r_gap = 25e3 # Gap in the outer ring
    n_segments = 2
    s = 10e3 # Gap between two pads of a central capacitor
    alpha = pi/4 # period of a gap zigzag
    r_curve = 30e3 # curvature of the roundings at the edges of a zigzag
    n_pts_cwave = 200

    Z1 = Zl # Parameters of a top CPW
    d_alpha1 = 0 # width of a tip of a central conductor of the top CPW
    width1 = 0 # width of a conductor in the bottom semiring
    gap1 = r_gap - 1.33e3 # gap between the bottom semiring and the central capacitor
    Z2 = Z # Paramters of a bottom CPW
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
                  
    p = p1 + DPoint( (p2-p1).x, (p2-p1).y/2 )
    sfs = SFS_Csh_emb( p, params + pars_squid, trans_in=Trans.R180 )
    sfs.place(cell, layer_ph,layer_el )
    
    sfs_line_in = CPW_RL_Path( p1, "LRL", Zl, cpw_curve, [(p2-p1).x,(p2-p1).y/2-r_out], pi/2 )
    sfs_line_in.place( cell, layer_ph )
    
    sfs_line_out = CPW( Z.width, Z.gap, sfs.connections[1], p2 )
    sfs_line_out.place( cell, layer_ph )
    # Single photon source drawing END #
    
    ## probe qubit drawing section START ##
    p1 = chip.connections[3]
    p2 = chip.connections[4]
    probe_line = CPW_RL_Path( p1, "LRLRL", Z, cpw_curve, [chip.chip_y/10,(p2-p1).x,chip.chip_y/10], [pi/2,pi/2], trans_in=Trans.R270 )
    probe_line.place( cell, layer_ph )
    
    N_probes = 3
    to_line = 40e3
    for i in range(N_probes):
        dx = abs( (p1-p2).x )/(N_probes + 1)
        dy = abs( chip.chip_y/10 )
        p = p1 + DPoint( dx*(i+1), -dy - to_line - r_out )
        sfs = SFS_Csh_emb( p, params + pars_squid, trans_in=Trans.R180 )
        sfs.place(cell, layer_ph,layer_el )
    ## probe qubit drawing section END ##
    
    ## Check resonators drawing section START ##
    p1 = chip.connections[5]
    p2 = chip.connections[7]
    probe_line = CPW_RL_Path( p1, "LRLRL", Z, cpw_curve, [chip.chip_y/10,abs((p1-p2).x),chip.chip_y/10], [-pi/2,-pi/2], trans_in=Trans.R90 )
    probe_line.place( cell, layer_ph )
    
    L_coupling = 300e3
    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L1_list = [261653., 239550., 219456., 201109]
    r = 50e3
    L2 = 270e3
    gnd_width = 35e3
    N = 4
    width_res = 9.6e3
    gap_res = 5.2e3
    to_line = 40e3
    Z_res = CPW( width_res, gap_res, origin, origin )
    worms = []
    N_res = 4
    for i in range(N_res):
        dx = abs( (p1-p2).x*(2/3)/(N_res) )
        worm = EMResonator_TL2Qbit_worm( Z_res, p1 + DPoint( abs((p1- p2).x/3) + (i)*dx, chip.chip_y/10 + to_line ),
                                                                L_coupling, L1_list[i], r, L2, N, trans_in=Trans.R180 )
        worm.place( cell, layer_ph )
        worms.append( worm )
    ## Check resonators drawing section END ##
    '''
    Z_rand = CPW( Z.width, Z.gap, worms[0].connections[1], p2 )
    Z_rand.place( cell, layer_ph )
    '''
    ### DRAW SECTION END ###
    
    lv.zoom_fit()
