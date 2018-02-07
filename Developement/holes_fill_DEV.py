import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib import * 

import sys

def fill_holes( obj, dx=10e3, dy=8e3, width=5e3, height=5e3, d=0 ):
    if( obj.is_cell_inst() ):
        return None
    poly = obj.shape.polygon
    bbox = poly.bbox()
    poly_reg = Region( poly )
    t_reg = Region()
    
    y = bbox.p1.y + height
    while( y < bbox.p2.y - height ):
        x = bbox.p1.x + width
        while( x < bbox.p2.x -  width ):
            box = pya.Box().from_dbox( pya.DBox(DPoint(x,y), DPoint(x + width,y + height)) )
            x += dx
            t_reg.clear()
            t_reg.insert( box )
            qwe = t_reg.select_inside( poly_reg )
            if( qwe.is_empty() ):
                continue
            edge_pairs = qwe.inside_check( poly_reg, d )
            if( edge_pairs.is_empty() ):
                poly.insert_hole( box )
        y += dy       
    obj.shape.polygon = poly


# Enter your Python code here
### MAIN FUNCTION ###
if __name__ == "__main__":
# getting main references of the application
    app = pya.Application.instance()
    mw = app.main_window()
    lv = mw.current_view()
    cv = lv.active_cellview()
    cell = cv.cell
    layout = cv.layout()

    if( lv.has_object_selection() ):
        selected = lv.object_selection
    else:
        pya.MessageBox.warning( "Script is not executed", "Please, select the shapes first", pya.MessageBox.Ok )
        sys.exit(0)
    

    for obj in selected:
        fill_holes( obj )
    lv.object_selection = selected
    ### DRAW SECTION START ###
    
    ### DRAW SECTION END ###
    
    lv.zoom_fit()