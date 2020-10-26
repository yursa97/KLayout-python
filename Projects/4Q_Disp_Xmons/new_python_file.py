# Enter your Python code here
from math import cos, sin, atan2, pi
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
import classLib
reload(classLib)

from classLib.baseClasses import ComplexBase, ElementBase
reload(classLib.coplanars)    
from classLib.coplanars import CPW, CPWParameters, CPW_RL_Path, CPW_arc, Coil_type_1, CPW2CPW

#from classLib.contactPads import ContactPad
from classLib.resonators import EMResonatorTL3QbitWormRLTailXmonFork
#from classLib.FluxCoil import *
#from Projects.4Q_Disp_Xmons.Xmon_C1_v2 import XmonCross

class XmonCross(ComplexBase):
    def __init__(self, origin,
                 sideX_length, sideX_width, sideX_gnd_gap, sideX_face_gnd_gap=None,
                 sideY_length=None, sideY_width=None, sideY_gnd_gap=None, sideY_face_gnd_gap=None,
                 trans_in=None):
        self.sideX_length = sideX_length
        self.sideY_length = None
        if sideY_length is None:
            self.sideY_length = self.sideX_length
        else:
            self.sideY_length = sideY_length

        self.sideX_width = sideX_width
        self.sideY_width = None
        if sideY_width is None:
            self.sideY_width = self.sideX_width
        else:
            self.sideY_width = sideY_width

        self.sideX_gnd_gap = sideX_gnd_gap
        self.sideY_gnd_gap = None
        if sideY_gnd_gap is None:
            self.sideY_gnd_gap = self.sideX_gnd_gap
        else:
            self.sideY_gnd_gap = sideY_gnd_gap

        if sideX_face_gnd_gap is None:
            self.sideX_face_gnd_gap = self.sideX_gnd_gap
        else:
            self.sideX_face_gnd_gap = sideX_face_gnd_gap

        if sideY_face_gnd_gap is None:
            self.sideY_face_gnd_gap = self.sideX_face_gnd_gap
        else:
            self.sideY_face_gnd_gap = self.sideY_face_gnd_gap

        # for saving
        self.center = origin
        super().__init__(origin, trans_in)
        self._geometry_parameters["sideX_length, um"] = self.sideX_length / 1e3
        self._geometry_parameters["sideY_length, um"] = self.sideY_length / 1e3
        self._geometry_parameters["sideX_width, um"] = self.sideX_width / 1e3
        self._geometry_parameters["sideY_width, um"] = self.sideY_width / 1e3
        self._geometry_parameters["sideX_gnd_gap, um"] = self.sideX_gnd_gap / 1e3
        self._geometry_parameters["sideY_gnd_gap, um"] = self.sideY_gnd_gap / 1e3
        self._geometry_parameters["sideX_face_gnd_gap, um"] = self.sideX_face_gnd_gap / 1e3
        self._geometry_parameters["sideY_face_gnd_gap, um"] = self.sideY_face_gnd_gap / 1e3
        self.center = self.connections[0]

    def init_primitives(self):
        origin = DPoint(0, 0)

        # draw central square
        from classLib.shapes import Rectangle
        lb_corner = DPoint(-self.sideX_width / 2, -self.sideY_width / 2)
        center_square = Rectangle(lb_corner, self.sideX_width, self.sideY_width)
        self.primitives["center_square"] = center_square

        """ left part of Xmon cross """
        p1 = origin + DPoint(-self.sideY_width / 2, 0)
        p2 = p1 + DPoint(-self.sideX_length, 0)
        self.cpw_l = CPW(self.sideX_width, self.sideX_gnd_gap, p1, p2)
        self.primitives["cpw_l"] = self.cpw_l
        p3 = p2 + DPoint(-self.sideX_face_gnd_gap, 0)
        self.cpw_lempt = CPW(0, self.cpw_l.b / 2, p2, p3)
        self.primitives["cpw_lempt"] = self.cpw_lempt

        """ right part of Xmon cross """
        p1 = origin + DPoint(self.sideY_width / 2, 0)
        p2 = p1 + DPoint(self.sideX_length, 0)
        self.cpw_r = CPW(self.sideX_width, self.sideX_gnd_gap, p1, p2)
        self.primitives["cpw_r"] = self.cpw_r
        p3 = p2 + DPoint(self.sideX_face_gnd_gap, 0)
        self.cpw_rempt = CPW(0, self.cpw_r.b / 2, p2, p3)
        self.primitives["cpw_rempt"] = self.cpw_rempt

        """ top part of Xmon cross """
        p1 = origin + DPoint(0, self.sideX_width / 2)
        p2 = p1 + DPoint(0, self.sideY_length)
        self.cpw_t = CPW(self.sideY_width, self.sideY_gnd_gap, p1, p2)
        self.primitives["cpw_t"] = self.cpw_t
        p3 = p2 + DPoint(0, self.sideY_face_gnd_gap)
        self.cpw_tempt = CPW(0, self.cpw_t.b / 2, p2, p3)
        self.primitives["cpw_tempt"] = self.cpw_tempt

        """ bottom part of Xmon cross """
        p1 = origin + DPoint(0, -self.sideX_width / 2)
        p2 = p1 + DPoint(0, -self.sideY_length)
        self.cpw_b = CPW(self.sideY_width, self.sideY_gnd_gap, p1, p2)
        self.primitives["cpw_b"] = self.cpw_b
        p3 = p2 + DPoint(0, -self.sideY_face_gnd_gap)
        self.cpw_bempt = CPW(0, self.cpw_b.b / 2, p2, p3)
        self.primitives["cpw_bempt"] = self.cpw_bempt

        self.connections = [origin]

class ContactPad(ComplexBase):
    def __init__(self, origin, pcb_cpw_params=CPWParameters(width=200e3, gap=120e3),
                 chip_cpw_params=CPWParameters(width=24.1e3, gap=12.95e3),
                 pad_length=300e3, back_metal_width=0, back_metal_gap=None,
                 transition_len=150e3,
                 trans_in=None):

        self.pcb_cpw_params: CPWParameters = pcb_cpw_params
        self.chip_cpw_params: CPWParameters = chip_cpw_params
        self.pad_length = pad_length
        self.back_metal_length = back_metal_width
        if back_metal_gap is not None:
            self.back_metal_gap = back_metal_gap
        else:
            self.back_metal_gap = self.pcb_cpw_params.gap
        self.transition_length = transition_len

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]

    def init_primitives(self):
        origin = DPoint(0, 0)

        # place metal between pad and PCB-chip edge
        self.cpw_back_metal = CPW(
            self.pcb_cpw_params.b, 0,
            start=origin, end=origin + DPoint(self.back_metal_length, 0)
        )
        self.primitives["cpw_back_metal"] = self.cpw_back_metal

        # erase metal between previous metal structure and pad-pcb face
        self.cpw_back_gap = CPW(
            0, self.pcb_cpw_params.b / 2,
            start=self.cpw_back_metal.end,
            end=self.cpw_back_metal.end + DPoint(self.back_metal_gap, 0)
        )
        self.primitives["cpw_back_gap"] = self.cpw_back_gap

        # place PCB-matching pad
        self.cpw_pcb_match = CPW(
            start=self.cpw_back_gap.end,
            end=self.cpw_back_gap.end + DPoint(self.pad_length, 0),
            cpw_params=self.pcb_cpw_params
        )
        self.primitives["cpw_pcb_match"] = self.cpw_pcb_match

        # PCB-match to on-chip waveguide trapeziod adapter
        self.cpw2cpw = CPW2CPW(
            self.pcb_cpw_params,
            self.chip_cpw_params,
            start=self.cpw_pcb_match.end,
            end=self.cpw_pcb_match.end + DPoint(self.transition_length, 0)
        )
        self.primitives["cpw2cpw"] = self.cpw2cpw

        self.connections = [origin, self.cpw2cpw.end]
        self.angle_connections = [0, self.cpw2cpw.alpha_end]
        
        
class FluxCoil(ElementBase):

    def __init__(self, origin, fc_cpw_params, width, trans_in = None):  # width = 5e3

        self._fc_cpw_params = fc_cpw_params
        self._width = width

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]


    def init_regions(self):

        w_fc, g_fc = self._fc_cpw_params.width, self._fc_cpw_params.gap

        empty_points = [DPoint(w_fc/2, 0),
                DPoint(w_fc/2, w_fc),
                DPoint(-self._width/2, w_fc),
                DPoint(-self._width/2, w_fc+g_fc),
                DPoint(self._width/2, w_fc+g_fc),
                DPoint(self._width/2, w_fc),
                DPoint(w_fc/2+g_fc, w_fc),
                DPoint(w_fc/2+g_fc, 0)]

        empty_region = Region(DSimplePolygon(empty_points))
        self.empty_region.insert(empty_region)

        self.connections = [DPoint(0,0), DPoint(0, w_fc+g_fc)]


class MDrive(ElementBase):

    def __init__(self, origin, fc_cpw_params, width, trans_in = None):  

        self._fc_cpw_params = fc_cpw_params
        self._width = width

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]


    def init_regions(self):

        w_fc, g_fc = self._fc_cpw_params.width, self._fc_cpw_params.gap

        empty_points = [DPoint(w_fc/2, 0),
                DPoint(self._width/2,0),
                DPoint(self._width/2, w_fc),
                DPoint(-self._width/2, w_fc),
                DPoint(-self._width/2,0),
                DPoint(-w_fc/2-g_fc,0),
                DPoint(-w_fc/2-g_fc, w_fc+g_fc),
                DPoint(w_fc/2+g_fc, w_fc+g_fc),
                DPoint(w_fc/2+g_fc, 0)]

        empty_region = Region(DSimplePolygon(empty_points))
        self.empty_region.insert(empty_region)

        self.connections = [DPoint(0,0), DPoint(0, w_fc+g_fc)]


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
    ro_line_dy = 1700e3  # 1000e3
    Z0 = CPWParameters(CHIP.cpw_width, CHIP.cpw_gap)
    cpwrl_ro = CPW_RL_Path(
        contact_pads[-1].end, shape="LRLRLRLRL", cpw_parameters=Z0,
        turn_radiuses=[ro_line_turn_radius] * 4,
        segment_lengths=[ro_line_dy, CHIP.pcb_feedline_d*2-CHIP.pcb_feedline_d/2+250e3+ 450e3,ro_line_dy/2,CHIP.pcb_feedline_d/2+250e3+ 450e3,ro_line_dy/2],
        turn_angles=[ pi / 2, pi / 2, pi / 2, -pi / 2], trans_in=Trans.R270
    )
    cpwrl_ro.place(tmp_reg)
    

    # resonators parameters
    L_coupling_list = [270e3] * 5
    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L0 = 1600e3 
    L1_list = [1e3 * x for x in [86.3011, 79.9939, 73.8822, 67.9571, 62.2103]]
    estimated_res_freqs_init = [4.932, 5.0, 5.08, 5.16, 5.24]  # GHz
    freqs_span_corase = 1.0  # GHz
    freqs_span_fine = 0.005
    r = 50e3
    N = 7
    L2_list = [r] * len(L1_list)
    L3_list = [0e3] * len(L1_list)
    L4_list = [r] * len(L1_list)
    width_res = 20e3
    gap_res = 10e3
    Z_res = CPW(width_res, gap_res, origin, origin)


    # xmon cross parameters
    cross_width = 60e3
    cross_len = 60e3 
    cross_gnd_gap = 20e3
    xmon_x_distance =453e3
        
    cross_len_x = 165e3
    cross_width_x = 60e3
    cross_width_y = 60e3
    cross_len_y = 60e3 
    cross_gnd_gap_x = 20e3
    cross_gnd_gap_y = 20e3
        
    #parametres for coplanar lines
    shift_fl_y = cross_len + 70e3
    shift_md_x = 175e3
    shift_md_y = 110e3
    # fork at the end of resonator parameters
    fork_metal_width = 20e3
    fork_gnd_gap = 20e3
    xmon_fork_gnd_gap = 20e3
    fork_x_span = cross_width + 2 * (xmon_fork_gnd_gap + fork_metal_width)
    fork_y_span = None
    # Xmon-fork parameters
    # -20e3 for Xmons in upper sweet-spot
    # -10e3 for Xmons in lower sweet-spot
    xmon_fork_penetration_list = [-20e3, -10e3, -20e3, -10e3, -20e3]

    photo_reg = Region()  # optimal to place everything in one region
    to_line_list = [53e3] * len(L1_list)

    ### RESONATORS TAILS CALCULATIONS SECTION START ###
    # key to the calculations can be found in hand-written format here:
    # https://drive.google.com/file/d/1wFmv5YmHAMTqYyeGfiqz79a9kL1MtZHu/view?usp=sharing

    # distance between nearest resonators central conductors centers
    resonators_d = 400e3
    # x span between left long vertical line and
    # right-most center of central conductors
    resonators_widths = [2 * r + L_coupling for L_coupling in L_coupling_list]
    x1 = sum(resonators_widths[:2]) + 2 * resonators_d + resonators_widths[3] / 2 - 2 * xmon_x_distance
    x2 = x1 + xmon_x_distance - (resonators_widths[0] + resonators_d)
    x3 = sum(resonators_widths[:3]) + 3 * resonators_d - (x1 + 3 * xmon_x_distance)
    x4 = sum(resonators_widths[:4]) + 4 * resonators_d - (x1 + 4 * xmon_x_distance)

    res_tail_shape = "LRLRL"
    tail_turn_radiuses = r

    L2_list[0] += 6 * Z_res.b
    L2_list[1] += 0
    L2_list[3] += 3 * Z_res.b
    L2_list[4] += 6 * Z_res.b

    L4_list[1] += 6 * Z_res.b
    L4_list[2] += 6 * Z_res.b
    L4_list[3] += 3 * Z_res.b
    tail_segment_lengths_list = [
        [L2_list[0], x1, L4_list[0]],
        [L2_list[1], x2, L4_list[1]],
        [L2_list[2], (L_coupling_list[2] + 2 * r) / 2, L4_list[2]],
        [L2_list[3], x3, L4_list[3]],
        [L2_list[4], x4, L4_list[4]]
    ]
    tail_turn_angles_list = [
        [pi / 2, -pi / 2],
        [pi / 2, -pi / 2],
        [pi / 2, -pi / 2],
        [-pi / 2, pi / 2],
        [-pi / 2, pi / 2],
    ]
    tail_trans_in_list = [
        Trans.R270,
        Trans.R270,
        Trans.R270,
        Trans.R270,
        Trans.R270
    ]
    ### RESONATORS TAILS CALCULATIONS SECTION END ###

    pars = list(
        zip(
            L1_list, estimated_res_freqs_init,
            to_line_list, L_coupling_list,
            xmon_fork_penetration_list,
            tail_segment_lengths_list, tail_turn_angles_list, tail_trans_in_list
        )
    )
    for res_idx, params in enumerate(pars):
        # parameters exctraction
        L1 = params[0]
        estimated_freq = params[1]
        to_line = params[2]
        L_coupling = params[3]
        xmon_fork_penetration = params[4]
        tail_segment_lengths = params[5]
        tail_turn_angles = params[6]
        tail_trans_in = params[7]
        fork_y_span = xmon_fork_penetration + xmon_fork_gnd_gap
        worm_x = None

        # deduction for resonator placements
        # under condition that Xmon-Xmon distance equals
        # `xmon_x_distance`
        worm_x = 1.15 * CHIP.pcb_feedline_d + \
                 sum(resonators_widths[:res_idx]) + res_idx*resonators_d + 450e3
        worm_y = contact_pads[-1].end.y - ro_line_dy - to_line

        worm = EMResonatorTL3QbitWormRLTailXmonFork(
            Z_res, DPoint(worm_x, worm_y), L_coupling, L0, L1, r, N,
            tail_shape=res_tail_shape, tail_turn_radiuses=r,
            tail_segment_lengths=tail_segment_lengths,
            tail_turn_angles=tail_turn_angles, tail_trans_in=tail_trans_in,
            fork_x_span=fork_x_span, fork_y_span=fork_y_span,
            fork_metal_width=fork_metal_width, fork_gnd_gap=fork_gnd_gap
        )

        xmon_center = (worm.fork_y_cpw1.end + worm.fork_y_cpw2.end) / 2
        xmon_center += DPoint(0, -(cross_len + cross_width / 2) + xmon_fork_penetration)
        xmonCross = XmonCross(xmon_center, cross_len_x, cross_width_x, cross_gnd_gap_x,
            sideY_length=cross_len_y, sideY_gnd_gap=cross_gnd_gap_y)

        # translating all objects so that chip.p1 at coordinate origin
        xmonCross.place(cell, layer_photo)
        worm.place(tmp_reg)

#        xmonCross_corrected = XmonCross(xmon_center, cross_width, cross_len, xmon_fork_gnd_gap)
        xmonCross_corrected = XmonCross(xmon_center, cross_len_x, cross_width_x, cross_gnd_gap_x,
            sideY_length=cross_len_y, sideY_gnd_gap=cross_gnd_gap_y)
        xmonCross_corrected.place(tmp_reg)
      
    #place caplanar line 1md
    cpwrl_ro1 = CPW_RL_Path(
        contact_pads[0].end, shape="LRLRLRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*3,
        segment_lengths=[2*(-contact_pads[0].end.x+xmon_center.x-4*xmon_x_distance)/16,((4*(contact_pads[0].end.y-xmon_center.y)/3)**2+(11*(-contact_pads[0].end.x+xmon_center.x-4*xmon_x_distance)/16)**2)**0.5-400e3,(((contact_pads[0].end.y-xmon_center.y)/3)**2+((-contact_pads[0].end.x+xmon_center.x-4*xmon_x_distance)/16)**2)**0.5,(-contact_pads[0].end.x+xmon_center.x-4*xmon_x_distance)/16],
        turn_angles=[-atan2(4*(contact_pads[0].end.y-xmon_center.y)/3,11*(-contact_pads[0].end.x+xmon_center.x-4*xmon_x_distance)/16),pi/2,-pi/2+atan2(4*(contact_pads[0].end.y-xmon_center.y)/3,11*(-contact_pads[0].end.x+xmon_center.x-4*xmon_x_distance)/16)], trans_in=Trans.R0
    )
    cpwrl_ro1.place(tmp_reg)

    cpwrl_ro1_end = MDrive(cpwrl_ro1.end, Z_res, width = 14e3, trans_in = Trans.R270)
    cpwrl_ro1_end.place(tmp_reg)

    #place caplanar line 1 fl
    cpwrl_ro2 = CPW_RL_Path(
        contact_pads[1].end, shape="LRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius],
        segment_lengths=[(-contact_pads[1].end.x+xmon_center.x-4*xmon_x_distance-cross_len_x) , (-contact_pads[1].end.y+xmon_center.y-cross_width_y/2-cross_gnd_gap_y-width_res)],
        turn_angles=[pi / 2], trans_in=Trans.R0
    )
    cpwrl_ro2.place(tmp_reg)

    cpwrl_ro2_end = FluxCoil(cpwrl_ro2.end, Z_res, width = 100e3, trans_in = Trans.R0)
    cpwrl_ro2_end.place(tmp_reg)

    #place caplanar line 2md
    cpwrl_ro3 = CPW_RL_Path(
        contact_pads[3].end, shape="LRLRLRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*3,
        segment_lengths=[(-contact_pads[3].end.y+xmon_center.y -shift_md_y)/4,(-contact_pads[3].end.x+xmon_center.x+shift_md_x-3*xmon_x_distance)/2,(((-contact_pads[3].end.x+xmon_center.x+shift_md_x-3*xmon_x_distance)/2)**2+(5*(-contact_pads[3].end.y+xmon_center.y -shift_md_y)/8)**2)**0.5,(-contact_pads[3].end.y+xmon_center.y -shift_md_y)/8],
        turn_angles=[-pi / 2,atan2(5*(-contact_pads[3].end.y+xmon_center.y -shift_md_y)/8,(-contact_pads[3].end.x+xmon_center.x+shift_md_x-3*xmon_x_distance)/2),pi/2-atan2(5*(-contact_pads[3].end.y+xmon_center.y -shift_md_y)/8,(-contact_pads[3].end.x+xmon_center.x+shift_md_x-3*xmon_x_distance)/2)], trans_in=Trans.R90
    )
    cpwrl_ro3.place(tmp_reg)

    cpwrl_ro3_end = MDrive(cpwrl_ro3.end, Z_res, width = 14e3, trans_in = Trans.R0)
    cpwrl_ro3_end.place(tmp_reg)

    #place caplanar line 2 fl
    cpwrl_ro4 = CPW_RL_Path(
        contact_pads[2].end, shape="LRLRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*2,
        segment_lengths=[(-contact_pads[2].end.x+xmon_center.x-3*xmon_x_distance)/4 ,((3*(-contact_pads[2].end.x+xmon_center.x-3*xmon_x_distance)/4)**2+(7*(-contact_pads[2].end.y+xmon_center.y-shift_fl_y)/8)**2)**0.5,(-contact_pads[2].end.y+xmon_center.y-shift_fl_y)/8],
        turn_angles=[atan2(7*(-contact_pads[2].end.y+xmon_center.y-shift_fl_y)/8,3*(-contact_pads[2].end.x+xmon_center.x-3*xmon_x_distance)/4),pi / 2-atan2(7*(-contact_pads[2].end.y+xmon_center.y-shift_fl_y)/8,3*(-contact_pads[2].end.x+xmon_center.x-3*xmon_x_distance)/4)], trans_in=Trans.R0
    )
    cpwrl_ro4.place(tmp_reg)

    cpwrl_ro4_end = FluxCoil(cpwrl_ro4.end, Z_res, width = 100e3, trans_in = Trans.R0)
    cpwrl_ro4_end.place(tmp_reg)

    #place caplanar line 3md
    cpwrl_ro5 = CPW_RL_Path(
        contact_pads[5].end, shape="LRLRLRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*3,
        segment_lengths=[(-contact_pads[5].end.y+xmon_center.y -shift_md_y)/4 , (contact_pads[5].end.x-xmon_center.x-shift_md_x+2*xmon_x_distance)/2,(((contact_pads[5].end.x-xmon_center.x-shift_md_x+2*xmon_x_distance)/2)**2+(5*(-contact_pads[5].end.y+xmon_center.y -shift_md_y)/8)**2)**0.5,(-contact_pads[5].end.y+xmon_center.y -shift_md_y)/8],
        turn_angles=[pi / 2,-atan2(5*(-contact_pads[5].end.y+xmon_center.y -shift_md_y)/8,(contact_pads[5].end.x-xmon_center.x-shift_md_x+2*xmon_x_distance)/2),-pi/2+atan2(5*(-contact_pads[5].end.y+xmon_center.y -shift_md_y)/8,(contact_pads[5].end.x-xmon_center.x-shift_md_x+2*xmon_x_distance)/2)], trans_in=Trans.R90
    )
    cpwrl_ro5.place(tmp_reg)

    cpwrl_ro5_end = MDrive(cpwrl_ro5.end, Z_res, width = 14e3, trans_in = Trans.R0)
    cpwrl_ro5_end.place(tmp_reg)

    #place caplanar line 3 fl
    cpwrl_ro6 = CPW_RL_Path(
        contact_pads[4].end, shape="L", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*0,
        segment_lengths=[(-contact_pads[4].end.y+xmon_center.y-shift_fl_y)],
        turn_angles=[], trans_in=Trans.R90
    )
    cpwrl_ro6.place(tmp_reg)

    cpwrl_ro6_end = FluxCoil(cpwrl_ro6.end, Z_res, width = 100e3, trans_in = Trans.R0)
    cpwrl_ro6_end.place(tmp_reg)


    #place caplanar line 4 md
    cpwrl_ro7 = CPW_RL_Path(
        contact_pads[7].end, shape="LRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius],
        segment_lengths=[contact_pads[7].end.x-xmon_center.x+xmon_x_distance -shift_md_x , -contact_pads[7].end.y+xmon_center.y-shift_md_y],
        turn_angles=[-pi / 2], trans_in=Trans.R180
    )
    cpwrl_ro7.place(tmp_reg)

    cpwrl_ro7_end = MDrive(cpwrl_ro7.end, Z_res, width = 14e3, trans_in = Trans.R0)
    cpwrl_ro7_end.place(tmp_reg)

    #place caplanar line 4 fl
    cpwrl_ro8 = CPW_RL_Path(
        contact_pads[6].end, shape="LRLRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*2,
        segment_lengths=[(contact_pads[6].end.x-xmon_center.x+xmon_x_distance)/4 , ((7*(-contact_pads[6].end.y+xmon_center.y-shift_fl_y)/8)**2+(3*(contact_pads[6].end.x-xmon_center.x+xmon_x_distance)/4)**2)**0.5,(-contact_pads[6].end.y+xmon_center.y-shift_fl_y)/8],
        turn_angles=[-atan2(7*(-contact_pads[6].end.y+xmon_center.y-shift_fl_y)/8,3*(contact_pads[6].end.x-xmon_center.x+xmon_x_distance)/4),-pi/2+atan2(7*(-contact_pads[6].end.y+xmon_center.y-shift_fl_y)/8,3*(contact_pads[6].end.x-xmon_center.x+xmon_x_distance)/4)], trans_in=Trans.R180
    )
    cpwrl_ro8.place(tmp_reg)

    cpwrl_ro8_end = FluxCoil(cpwrl_ro8.end, Z_res, width = 100e3, trans_in = Trans.R0)
    cpwrl_ro8_end.place(tmp_reg)

    #place caplanar line 5 md
    cpwrl_ro9 = CPW_RL_Path(
        contact_pads[9].end, shape="LRLRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*2,
        segment_lengths=[2*(contact_pads[9].end.y-xmon_center.y)/3-cross_gnd_gap_y-cross_width_y-20e3,(((contact_pads[9].end.y-xmon_center.y)/3)**2+(2*(contact_pads[9].end.x-xmon_center.x-cross_len_x- cross_width_x/2-cross_gnd_gap_x)/3)**2)**0.5 ,(contact_pads[9].end.x-xmon_center.x-cross_len_x- cross_width_x/2-cross_gnd_gap_x)/3+30e3],
        turn_angles=[-atan2(2*(contact_pads[9].end.x-xmon_center.x-cross_len_x- cross_width_x/2-cross_gnd_gap_x)/3,(contact_pads[9].end.y-xmon_center.y)/3),atan2(2*(contact_pads[9].end.x-xmon_center.x-cross_len_x- cross_width_x/2-cross_gnd_gap_x)/3,(contact_pads[9].end.y-xmon_center.y)/3)-pi / 2], trans_in=Trans.R270
    )
    cpwrl_ro9.place(tmp_reg)

    cpwrl_ro9_end = MDrive(cpwrl_ro9.end, Z_res, width = 14e3, trans_in = Trans.R90)
    cpwrl_ro9_end.place(tmp_reg)

    #place caplanar line 5 fl
    cpwrl_ro10 = CPW_RL_Path(
        contact_pads[8].end, shape="LRLRLRLRL", cpw_parameters=Z_res,
        turn_radiuses=[ro_line_turn_radius]*4,
        segment_lengths=[(contact_pads[8].end.x-xmon_center.x)/4, ((contact_pads[8].end.y-xmon_center.y)+250e3)/3+50e3,((2*((contact_pads[8].end.y-xmon_center.y)+250e3)/3)**2+((contact_pads[8].end.x-xmon_center.x)/2)**2)**0.5,(contact_pads[8].end.x-xmon_center.x)/4-cross_len_x,230e3 ],
        turn_angles=[pi / 2, -atan2((contact_pads[8].end.x-xmon_center.x)/2,2*((contact_pads[8].end.y-xmon_center.y)+250e3)/3),- pi/2+atan2((contact_pads[8].end.x-xmon_center.x)/2,2*((contact_pads[8].end.y-xmon_center.y)+250e3)/3),-pi / 2], trans_in=Trans.R180
    )
    cpwrl_ro10.place(tmp_reg)

    cpwrl_ro10_end = FluxCoil(cpwrl_ro10.end, Z_res, width = 100e3, trans_in = Trans.R0)
    cpwrl_ro10_end.place(tmp_reg)
    
    
    # convert region to cell and display it
    cell.shapes(layer_photo).insert(tmp_reg)
    lv.zoom_fit()
    ## DRAWING SECTION END ## 
