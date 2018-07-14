import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

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
    
    # Single photon source photo layer drawing START #
    r_out = 200e3
    r_gap = 0
    n_semiwaves = 4
    s = 5e3  
    alpha = pi/3
    r_curve = 10e3
    n_pts_cwave = 50
    L0 = 20e3
    delta = 30e3
    
    cwave_params = [r_out,r_gap,n_semiwaves,s,alpha,r_curve,delta,L0,n_pts_cwave]
    
    cap = CWave( origin, *cwave_params, trans_in=Trans.R90 )
    cap.place( cell, layer_ph )
    
    gap = 0
    width = 30e3
    length = 150e3
    delta = 10e3
    Z_left = CPW( width, gap, origin + DPoint( -r_out + delta,0 ), origin + DPoint( -r_out - length + delta,0 ) )
    Z_left.place( cell, layer_ph, merge=True )
    
    Z_right = CPW( width, gap, origin - DPoint( -r_out + delta,0 ), origin - DPoint( -r_out - length + delta,0 ) )
    Z_right.place( cell, layer_ph, merge=True )
    ### DRAW SECTION END ###
    
    lv.zoom_fit()