import pya
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region, Box, DBox
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload

import ClassLib
reload(ClassLib)
from ClassLib import *

import sonnetSim
reload(sonnetSim)
from sonnetSim import SonnetLab, SimulationResult

from itertools import product

def boxes_touching(box1, box2):
    """
    Tests, whether 2 boxes has at least 1 point in common
    and if there is common coordinates of the
    left, right, top or bottom sides (definition of touching for boxes)

    :param box1: pya.Box
    :param box2: pya.Box
    :return:
    """
    if( box1.touches(box2) and (box1.left == box2.left or
                                box1.right == box2.right or
                                box1.top == box2.top or
                                box1.bottom == box2.bottom) ):
        return True
    else:
        return False


def poly_design_from_selection( selected ):
    ret_design = Chip_Design()
    # using ret_design.region_ph as a storage for

    ground_polygons = []
    complete_bbox = Box()
    for obj in selected:
        if not obj.is_cell_inst():
            complete_bbox += obj.shape.bbox()
            ret_design.region_ph.insert(obj.shape.polygon)

    for obj in selected:
        if not obj.is_cell_inst():
            if boxes_touching(obj.shape.bbox(), complete_bbox):
                ground_polygons.append(obj.shape.polygon)
                print(obj.shape.polygon.bbox())


def find_capacitance2GND( poly1, poly_GND ):
    max_dist = 0
    min_dist = 0
    for p1, p2 in product(poly1.points, poly_GND.points ):
        dist = (p1-p2).abs() # euclidian distance
        min_dist = min(min_dist, dist )
        max_dist = max(max_dist, dist )
    print(min_dist, max_dist)


def find_mutual_capacitance( poly1, poly2, bbox ):
    pass

import sys
### MAIN FUNCTION ###
if __name__ == "__main__":
    SR = SimulationResult()
    app = pya.Application.instance()
    mw = app.main_window()
    lv = mw.current_view()

    if lv.has_object_selection():
        design = poly_design_from_selection(lv.object_selection)
    else:
        pya.MessageBox.warning("Script is not executed", "Please, select the shapes first", pya.MessageBox.Ok)
