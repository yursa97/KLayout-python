# Enter your Python code here
from math import cos, sin, atan2, pi
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from classLib.baseClasses import ComplexBase
from classLib.coplanars import CPW, CPW_arc
from classLib.resonators import Coil_type_1
from classLib.shapes import XmonCross
from classLib.resonators import EMResonator_TL2Qbit_worm3_XmonFork

#from sonnetSim.sonnetLab import SonnetLab, SonnetPort, SimulationBox

class CHIP:
    dx = 0.6e6
    dy = 2.5e6
    nX = 300  # simulation box cells along X-axis
    nY = 1250  # simulation box cells along Y-axis

    # connections of the chip (not used in this file)
    gap = 150.e3
    width = 260.e3
    b = 2 * gap + width
    origin = DPoint(0, 0)
    box = pya.DBox(origin, origin + DPoint(dx, dy))
    L1 = 220
    # only 4 connections programmed by now
    connections = [box.p1 + DPoint(L1 + b / 2, 0), box.p1 + DPoint(dx - (L1 + b / 2), 0),
                   box.p2 - DPoint(L1 + b / 2, 0), box.p1 + DPoint(L1 + b / 2, dy)]

    @staticmethod
    def get_geometry_params_dict(prefix="", postfix=""):
        from collections import OrderedDict
        geometry_params = OrderedDict(
            [
                ("dx, um", CHIP.dx / 1e3),
                ("dy, um", CHIP.dy / 1e3),
                ("nX", CHIP.nX),
                ("nY", CHIP.nY)
            ]
        )
        modified_dict = OrderedDict()
        for key, val in geometry_params.items():
            modified_dict[prefix + key + postfix] = val
        return modified_dict


if __name__ == "__main__":
    # getting main references of the application
    app = pya.Application.instance()
    mw = app.main_window()
    lv = mw.current_view()
    cv = None
    
    # this insures that lv and cv are valid objects
    if lv is None:
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
    
    layer_info_photo = pya.LayerInfo(10,0)
    layer_info_el = pya.LayerInfo(1,0)    
    layer_photo = layout.layer( layer_info_photo )
    layer_el = layout.layer( layer_info_el )

    # setting layout view  
    lv.select_cell(cell.cell_index(), 0)
    lv.add_missing_layers()

    
    ## DRAWING SECTION START ##
    origin = DPoint(0, 0)
    
    # main drive line coplanar
    width = 24.1e3
    gap = 12.95e3
    x = None
    y = 0.9 * CHIP.dy
    p1 = DPoint(0, y)
    p2 = DPoint(CHIP.dx, y)
    Z0 = CPW(width, gap, p1, p2)
    
    # resonator
    L_coupling = 200e3
    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L0 = 1700e3
    L1_list = [1e3*x for x in [79.3927, 75.5225, 71.7273, 68.0048, 64.353]]
    estimated_res_freqs = [5.0209, 5.0715, 5.1209, 5.1756, 5.2140]  # GHz
    freqs_span = 0.004  # GHz
    r = 50e3
    L2_list = [100e3 + 0.5*(L1_list[0] - L1) for L1 in L1_list]
    gnd_width = 35e3
    N = 7
    width_res = 10e3
    gap_res = 10e3
    to_line = 45e3
    Z_res = CPW(width_res, gap_res, origin, origin)

    # xmon cross parameters
    cross_width = 60e3
    cross_len = 125e3
    cross_gnd_gap = 20e3

    # fork at the end of resonator parameters
    fork_metal_width = 20e3
    fork_gnd_gap = 20e3
    xmon_fork_gnd_gap = 20e3
    fork_x_span = cross_width + 2 * (xmon_fork_gnd_gap + fork_metal_width)
    fork_y_span = None
    # Xmon-fork parameters
    # -20e3 for Xmons in upper sweet-spot
    # -10e3 for Xmons in lower sweet-spot
    xmon_fork_penetration = -20e3

    L_coupling = 200e3
    to_line_list = [46e3]
    pars = map(
        lambda x: list(x[0]) + [x[1]],
        itertools.product(zip(L1_list, L2_list, estimated_res_freqs), to_line_list)
    )
    for L1, L2, estimated_freq, to_line in pars:
        # clear this cell and layer
        cell.clear()
        fork_y_span = xmon_fork_penetration + xmon_fork_gnd_gap
        worm_x = CHIP.dx/2 - L_coupling/2
        worm = EMResonator_TL2Qbit_worm3_XmonFork(
            Z_res, DPoint(worm_x, y - to_line), L_coupling, L0, L1, r, L2, N,
            fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap
        )

        xmon_center = (worm.fork_y_cpw1.end + worm.fork_y_cpw2.end) / 2
        xmon_center += DPoint(0, -(cross_len + cross_width / 2) + xmon_fork_penetration)
        xmonCross = XmonCross(xmon_center, cross_width, cross_len, cross_gnd_gap)

        # calculate simulation box dimensions
        chip_box = pya.Box(DPoint(0, 0), DPoint(CHIP.dx, CHIP.dy))

        # placing all objects in proper order and translating them to origin
        cell.shapes(layer_photo).insert(chip_box)

        # translating all objects so that chip.p1 at coordinate origin
        xmonCross.place(cell, layer_photo)
        worm.place(cell, layer_photo)

        xmonCross_corrected = XmonCross(xmon_center, cross_width, cross_len, xmon_fork_gnd_gap)
        xmonCross_corrected.place(cell, layer_photo)
        
        Z0.place(cell, layer_photo)

        # delete Xmon cross
        shapes = cell.shapes(layer_photo)
        for shape in shapes.each_overlapping(pya.Box(xmon_center, xmon_center)):
            # if shape is polygon and contains xmon_center inside
            # then delete this polygon
            if shape.is_polygon and shape.polygon.inside(xmon_center):
                shape.delete()

        ## DRAWING SECTION END ##
        lv.zoom_fit()

