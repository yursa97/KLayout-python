# Enter your Python code here
from math import cos, sin, atan2, pi
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
import ClassLib
reload(ClassLib)

from ClassLib.Coplanars import CPW, CPWParameters, CPW_RL_Path
from ClassLib.Shapes import XmonCross
from ClassLib.contactPads import ContactPad

from ClassLib.Resonators import EMResonator_TL2Qbit_worm3_2_XmonFork


class CHIP:
    """
    10x10 mm chip
    PCB design located here:
    https://drive.google.com/drive/folders/1TGjD5wwC28ZiLln_W8M6gFJpl6MoqZWF?usp=sharing
    """
    dx = 10e6
    dy = 10e6

    pcb_width = 260e3  # 0.26 mm
    pcb_gap = 190e3  # (0.64 - 0.26) / 2 = 0.19 mm
    pcb_feedline_d = 2500e3  # 2.5 mm
    pcb_Z = CPWParameters(pcb_width, pcb_gap)

    cpw_width = 24.1e3
    cpw_gap = 12.95e3
    chip_Z = CPWParameters(cpw_width, cpw_gap)

    @staticmethod
    def get_contact_pads():
        dx = CHIP.dx
        dy = CHIP.dy
        pcb_feedline_d = CHIP.pcb_feedline_d
        pcb_Z = CHIP.pcb_Z
        chip_Z = CHIP.chip_Z

        contact_pads_left = [
            ContactPad(
                DPoint(0, dy - pcb_feedline_d * (i + 1)), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3
            ) for i in range(3)
        ]

        contact_pads_bottom = [
            ContactPad(
                DPoint(pcb_feedline_d * (i + 1), 0), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3,
                trans_in=Trans.R90
            ) for i in range(3)
        ]

        contact_pads_right = [
            ContactPad(
                DPoint(dx, pcb_feedline_d*(i+1)), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3,
                trans_in=Trans.R180
            ) for i in range(3)
        ]

        contact_pads_top = [
            ContactPad(
                DPoint(dx - pcb_feedline_d * (i + 1), dy), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3,
                trans_in=Trans.R270
            ) for i in range(3)
        ]

        # contact pads are ordered starting with top-left corner in counter-clockwise direction
        contact_pads = itertools.chain(
            contact_pads_left, contact_pads_bottom,
            contact_pads_right, contact_pads_top
        )

        return list(contact_pads)

    origin = DPoint(0, 0)
    box = pya.DBox(origin, origin + DPoint(dx, dy))

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
    x = None
    y = 0.9 * CHIP.dy
    p1 = DPoint(0, y)
    p2 = DPoint(CHIP.dx, y)
    Z0 = CPW(CHIP.cpw_width, CHIP.cpw_gap, p1, p2)
    
    # resonator
    # corresponding to resonanse freq is somewhere near 5 GHz
    L_coupling_list = [270e3]*5
    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L0 = 1600e3
    L1_list = [1e3 * x for x in [86.3011, 79.9939, 73.8822, 67.9571, 62.2103]]
    estimated_res_freqs_init = [4.932, 5.0, 5.08, 5.16, 5.24]  # GHz
    freqs_span_corase = 1.0  # GHz
    freqs_span_fine = 0.005
    r = 50e3
    N = 7
    L2_list = [0.0e3] * len(L1_list)
    L3 = 0
    width_res = 20e3
    gap_res = 10e3
    Z_res = CPW(width_res, gap_res, origin, origin)
    to_line = 55e3

    # xmon cross parameters
    cross_width = 60e3
    cross_len = 125e3
    cross_gnd_gap = 20e3
    xmon_x_distance = 393e3  # from simulation of g_12

    # fork at the end of resonator parameters
    fork_metal_width = 20e3
    fork_gnd_gap = 20e3
    xmon_fork_gnd_gap = 20e3
    fork_x_span = cross_width + 2 * (xmon_fork_gnd_gap + fork_metal_width)
    fork_y_span = None
    # Xmon-fork parameters
    # -20e3 for Xmons in upper sweet-spot
    # -10e3 for Xmons in lower sweet-spot
    import itertools
    xmon_fork_penetrations = [-20e3, -10e3, -20e3, -10e3, -20e3]

    # clear this cell and layer
    cell.clear()
    tmp_reg = Region()  # faster to call `place` on single region

    # place chip metal layer
    chip_box = pya.Box(DPoint(0, 0), DPoint(CHIP.dx, CHIP.dy))
    tmp_reg.insert(chip_box)
    contact_pads = CHIP.get_contact_pads()
    for contact_pad in contact_pads:
        contact_pad.place(tmp_reg)

    # place readout waveguide
    ro_line_turn_radius = 200e3
    ro_line_dy = 600e3
    cpwrl_ro = CPW_RL_Path(
        contact_pads[-1].end, shape="LRLRL", cpw_parameters=Z0,
        turn_radiuses=[ro_line_turn_radius]*2,
        segment_lengths=[ro_line_dy, CHIP.pcb_feedline_d, ro_line_dy],
        turn_angles=[pi/2, pi/2], trans_in=Trans.R270
    )
    cpwrl_ro.place(tmp_reg)

    params = zip(L1_list, L2_list, L_coupling_list, xmon_fork_penetrations)
    for res_idx, (L1, L2, L_coupling, xmon_fork_penetration) in enumerate(params):
        fork_y_span = xmon_fork_penetration + xmon_fork_gnd_gap
        worm_x = None

        # deduction for resonator placements
        # under condition that Xmon-Xmon distance equals
        # `xmon_x_distance`
        if res_idx == 0:
            worm_x = 1.2*CHIP.pcb_feedline_d
        else:
            worm_x = 1.2*CHIP.pcb_feedline_d + res_idx * xmon_x_distance - \
                     (L_coupling_list[res_idx] - L_coupling_list[0]) + \
                     (L1_list[res_idx] - L1_list[0])/2
        worm_y = contact_pads[-1].end.y - ro_line_dy - to_line

        worm = EMResonator_TL2Qbit_worm3_2_XmonFork(
            Z_res, DPoint(worm_x, worm_y), L_coupling, L0, L1, r, L2, N,
            fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap
        )

        xmon_center = (worm.fork_y_cpw1.end + worm.fork_y_cpw2.end) / 2
        xmon_center += DPoint(0, -(cross_len + cross_width / 2) + xmon_fork_penetration)
        xmonCross = XmonCross(xmon_center, cross_width, cross_len, cross_gnd_gap)

        # translating all objects so that chip.p1 at coordinate origin
        xmonCross.place(cell, layer_photo)
        worm.place(tmp_reg)

        xmonCross_corrected = XmonCross(xmon_center, cross_width, cross_len, xmon_fork_gnd_gap)
        xmonCross_corrected.place(tmp_reg)

    # convert region to cell and display it
    cell.shapes(layer_photo).insert(tmp_reg)
    lv.zoom_fit()
    ## DRAWING SECTION END ##