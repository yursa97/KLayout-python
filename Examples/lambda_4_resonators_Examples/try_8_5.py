# Enter your Python code here
from math import cos, sin, atan2, pi
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from classLib.baseClasses import ComplexBase
from classLib.coplanars import CPW, CPW_arc
from classLib.resonators import Coil_type_1
from classLib.shapes import XmonCross

from classLib.resonators import EMResonator_TL2Qbit_worm4_XmonFork

# NOT TESTED, ERRORS CAN BE FIGURED OUT EASILY

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
    if (layout.has_cell("testScript")):
        pass
    else:
        cell = layout.create_cell("testScript")

    layer_info_photo = pya.LayerInfo(10, 0)
    layer_info_el = pya.LayerInfo(1, 0)
    layer_photo = layout.layer(layer_info_photo)
    layer_el = layout.layer(layer_info_el)

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
    # corresponding to resonanse freq is somewhere near 5 GHz
    # resonator
    L_coupling = 200e3
    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L0 = 1700e3
    L1_list = [1e3 * x for x in [79.3927, 75.5225, 71.7273, 68.0048, 64.353]]
    estimated_res_freqs = [5.0209, 5.0715, 5.1209, 5.1756, 5.2140]  # GHz
    disp = -0.040  # GHz
    estimated_res_freqs = [freq - disp for freq in estimated_res_freqs]
    freqs_span = 0.080  # GHz
    r = 50e3
    L2_list = [100e3 + 0.5 * (L1_list[0] - L1) for L1 in L1_list]
    N = 7
    width_res = 10e3
    gap_res = 10e3
    Z_res = CPW(width_res, gap_res, origin, origin)
    stab_width = 0e3
    stab_gnd_gap = 20e3
    stab_len = 0e3
    # stab_end_gnd_gap = 10e3

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
    to_line_list = [1e3*x for x in [150]]
    pars = map(
        lambda x: list(x[0]) + [x[1]],
        itertools.product(zip(L1_list, L2_list, estimated_res_freqs), to_line_list)
    )
    photo_reg = Region()

    for L1, L2, estimated_freq, to_line in list(pars)[:1]:
        # clear this cell and layer
        cell.clear()
        fork_y_span = xmon_fork_penetration + xmon_fork_gnd_gap
        worm_x = CHIP.dx / 2 - L_coupling / 2
        stab_end_gnd_gap = to_line - Z_res.width/2 - Z0.b/2  # exactly to create empty coridor to the waveguide
        # for stability (in case float will be rounded badly and this will result in 1 nm ground between resonator stab and waveguide
        stab_end_gnd_gap += Z0.gap/2
        worm = EMResonator_TL2Qbit_worm4_XmonFork(
            Z_res, DPoint(worm_x, y - to_line), L_coupling, L0, L1, r, L2, N,
            stab_width, stab_gnd_gap, stab_len, stab_end_gnd_gap,
            fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap
        )

        xmon_center = (worm.fork_y_cpw1.end + worm.fork_y_cpw2.end) / 2
        xmon_center += DPoint(0, -(cross_len + cross_width / 2) + xmon_fork_penetration)
        xmonCross = XmonCross(xmon_center, cross_width, cross_len, cross_gnd_gap)

        # waveguide-resonator coupling section
        tunnel_length = to_line - Z_res.b/2 - Z0.b/2
        tunnel_b = stab_width + 2*stab_gnd_gap
        block_width = 5e3
        block_path_gap = 5e3
        block_length = tunnel_b - block_path_gap
        n_blocks = 12
        blocks_list = []
        for i in range(n_blocks):
            m = 1 if i%2==0 else -1
            p1 = worm.Z_stab_end_empty.start + DPoint(-m*tunnel_b/2, Z_res.gap + block_width/2 + (block_path_gap + block_width)*i)
            p2 = p1 + DPoint(m*block_length, 0)
            cpw_block = CPW(block_width, 0, p1, p2)
            blocks_list.append(cpw_block)

        # calculate simulation box dimensions
        chip_box = pya.Box(DPoint(0, 0), DPoint(CHIP.dx, CHIP.dy))

        # placing all objects in proper order and translating them to origin
        photo_reg.insert(chip_box)

        # translating all objects so that chip.p1 at coordinate origin
        xmonCross.place(photo_reg)
        worm.place(photo_reg)
        for block in blocks_list:
            block.place(photo_reg)

        # correction needed for the Xmon to have proper gaps with resonator and ground
        xmonCross_corrected = XmonCross(xmon_center, cross_width, cross_len, xmon_fork_gnd_gap)
        xmonCross_corrected.place(photo_reg)

        Z0.place(photo_reg)

        cell.shapes(layer_photo).insert(photo_reg)

        # delete Xmon cross
        shapes = cell.shapes(layer_photo)
        for shape in shapes.each_overlapping(pya.Box(xmon_center, xmon_center)):
            # if shape is polygon and contains xmon_center inside
            # then delete this polygon
            if shape.is_polygon and shape.polygon.inside(xmon_center):
                shape.delete()

        lv.zoom_fit()
        ## DRAWING SECTION END ##
