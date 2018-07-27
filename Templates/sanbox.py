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
    Z_params = CPWParameters( 14.5e3, 6.7e3 )
    chip = Chip5x10_with_contactPads( origin, Z_params )
    chip.place( cell, layer_ph )

    gap = 0e3
    width = 30e3
    length = 150e3
    delta = 200e3
    Z_left = CPW( width, gap, origin + DPoint( 0, chip.chip_y/2 ), origin + DPoint( chip.chip_x/2, chip.chip_y/2 ) )
    Z_left.place( cell,layer_ph )
    ### DRAW SECTION END ###
    CPW()
    lv.zoom_fit()
