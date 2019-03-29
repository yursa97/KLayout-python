import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region, Path
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib import * 

import sys

""" 
    This helper draws a grid of holes for pinning vortices in a superconducting chip.
    In order to use this helper, select a shape or a few shapes in your chip
    and then run the script
"""

def fill_holes(cell, layer, obj, dx=15e3, dy=15e3, width=10e3, height=10e3, d=50e3 ):
    """ @brief:     Fills an object with a grid of holes
                    Warning: don't use this method for the same region twice
        @params:    cell
                    layer
                    obj
                    dx : int
                        period of a grid in horizonatal direction
                    dy : int
                        period of a grid in vertical direction
                    width : int
                        width of a hole
                    height : int
                        height of a hole
                    d : int
                        padding
    """
    if( obj.is_cell_inst() ):
        return None
    poly = obj.shape.polygon
    print(poly.holes())
    bbox = poly.bbox()
    poly_reg = Region( poly )
    t_reg = Region()
    
    # Fill the boundary box with holes
    y = bbox.p1.y + height
    while y < bbox.p2.y - height:
        x = bbox.p1.x + width
        while x < bbox.p2.x - width:
            box = pya.Box().from_dbox( pya.DBox(DPoint(x,y), DPoint(x + width,y + height)) )
            x += dx
            t_reg.insert( box )
        y += dy
  
    # Draw boundary around holes in the polygon
    for hole_i in range(0, poly.holes()):
        points = [p for p in poly.each_point_hole(hole_i)]
        points.append(points[0])
        boundary = Path(points, d)
        poly_reg -= Region(boundary)
    
    # Draw boundary around the outer edge of the polygon
    points = [p for p in poly.each_point_hull()]
    points.append(points[0])
    boundary = Path(points, d)
    poly_reg -= Region(boundary)
    
    # Select only inner holes
    qwe = t_reg.select_inside(poly_reg)

    # Subtract holes from the layer
    r_cell = Region(cell.begin_shapes_rec(layer))
    temp_i = cell.layout().layer(pya.LayerInfo(PROGRAM.LAYER1_NUM,0) )
    cell.shapes(temp_i).insert(r_cell - qwe)
    cell.layout().clear_layer(layer)
    cell.layout().move_layer(temp_i, layer)
    cell.layout().delete_layer(temp_i)

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
    
    layer_ph = layout.layer(pya.LayerInfo(1,0))
    for obj in selected:
        fill_holes(cell, layer_ph, obj)
    lv.object_selection = selected
    ### DRAW SECTION START ###
    
    ### DRAW SECTION END ###
    
    lv.zoom_fit()