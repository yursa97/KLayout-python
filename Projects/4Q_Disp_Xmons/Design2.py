# Enter your Python code here
from math import cos, sin, tan, atan2, pi
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
import classLib

reload(classLib)

from classLib.baseClasses import ElementBase
from classLib.coplanars import CPWParameters, CPW_RL_Path
from classLib.shapes import XmonCross
from classLib.resonators import EMResonatorTL3QbitWormRLTailXmonFork
from classLib.josJ import AsymSquidParams, AsymSquid
from classLib.chipTemplates import CHIP_10x10_12pads
from classLib.chipDesign import ChipDesign

# imports for docstrings generation
from typing import List, Dict
from classLib.contactPads import ContactPad


class FluxLineEnd(ElementBase):

    def __init__(self, origin, fc_cpw_params, width, trans_in=None):  # width = 5e3

        self._fc_cpw_params = fc_cpw_params
        self._width = width

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]

    def init_regions(self):
        w_fc, g_fc = self._fc_cpw_params.width, self._fc_cpw_params.gap

        empty_points = [DPoint(w_fc / 2, 0),
                        DPoint(w_fc / 2, w_fc),
                        DPoint(-self._width / 2, w_fc),
                        DPoint(-self._width / 2, w_fc + g_fc),
                        DPoint(self._width / 2, w_fc + g_fc),
                        DPoint(self._width / 2, w_fc),
                        DPoint(w_fc / 2 + g_fc, w_fc),
                        DPoint(w_fc / 2 + g_fc, 0)]

        empty_region = Region(DSimplePolygon(empty_points))
        self.empty_region.insert(empty_region)

        self.connections = [DPoint(0, 0), DPoint(0, w_fc + g_fc)]


class MDriveLineEnd(ElementBase):

    def __init__(self, origin, fc_cpw_params, width, trans_in=None):
        self._fc_cpw_params = fc_cpw_params
        self._width = width

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]

    def init_regions(self):
        w_fc, g_fc = self._fc_cpw_params.width, self._fc_cpw_params.gap

        empty_points = [DPoint(w_fc / 2, 0),
                        DPoint(self._width / 2, 0),
                        DPoint(self._width / 2, w_fc),
                        DPoint(-self._width / 2, w_fc),
                        DPoint(-self._width / 2, 0),
                        DPoint(-w_fc / 2 - g_fc, 0),
                        DPoint(-w_fc / 2 - g_fc, w_fc + g_fc),
                        DPoint(w_fc / 2 + g_fc, w_fc + g_fc),
                        DPoint(w_fc / 2 + g_fc, 0)]

        empty_region = Region(DSimplePolygon(empty_points))
        self.empty_region.insert(empty_region)

        self.connections = [DPoint(0, 0), DPoint(0, w_fc + g_fc)]


class Design5Q(ChipDesign):
    def __init__(self, cell_name):

        super().__init__(cell_name)
        info_el2 = pya.LayerInfo(3, 0)  # for DC contact deposition
        self.region_el2 = Region()
        self.layer_el2 = self.layout.layer(info_el2)

        info_bridges1 = pya.LayerInfo(4, 0)  # bridge photo layer 1
        self.region_bridges1 = Region()
        self.layer_bridges1 = self.layout.layer(info_bridges1)

        info_bridges2 = pya.LayerInfo(5, 0)  # bridge photo layer 2
        self.region_bridges2 = Region()
        self.layer_bridges2 = self.layout.layer(info_bridges2)

        self.lv.add_missing_layers()  # has to call it once more to add new layers

        ### ADDITIONAL VARIABLES SECTION START ###
        self.contact_pads: list[ContactPad] = None

        # readout line parameters
        self.ro_line_turn_radius: float = 200e3
        self.ro_line_dy: float = 1700e3
        self.cpwrl_ro_line: CPW_RL_Path = None
        self.Z0 = CPWParameters(CHIP_10x10_12pads.cpw_width, CHIP_10x10_12pads.cpw_gap)

        # resonators objects list
        self.resonators: List[EMResonatorTL3QbitWormRLTailXmonFork] = []
        # resonator parameters
        self.L_coupling_list = [1e3 * x for x in [255, 250, 250, 240, 230]]
        # corresponding to resonanse freq is linspaced in interval [6,9) GHz
        self.L0 = 1600e3
        self.L1_list = [1e3 * x for x in [37.7039, 67.6553, 90.925, 81.5881, 39.9021]]
        self.r = 60e3
        self.N = 5
        self.L2_list = [self.r] * len(self.L1_list)
        self.L4_list = [self.r] * len(self.L1_list)
        self.width_res = 20e3
        self.gap_res = 10e3
        self.Z_res = CPWParameters(self.width_res, self.gap_res)
        self.to_line_list = [53e3] * len(self.L1_list)
        self.fork_metal_width = 20e3
        self.fork_gnd_gap = 20e3
        self.xmon_fork_gnd_gap = 20e3
        # resonator-fork parameters
        # -20e3 for Xmons in upper sweet-spot
        # -10e3 for Xmons in lower sweet-spot
        self.xmon_fork_penetration_list = [-20e3, -10e3, -20e3, -10e3, -20e3]

        # xmon parameters
        self.cross_width: float = 60e3
        self.cross_len: float = 60e3
        self.cross_gnd_gap: float = 20e3
        self.xmon_x_distance: float = 453e3  # from simulation of g_12
        self.xmons: list[XmonCross] = []

        self.cross_len_x = 165e3
        self.cross_width_x = 60e3
        self.cross_width_y = 60e3
        self.cross_len_y = 60e3
        self.cross_gnd_gap_x = 20e3
        self.cross_gnd_gap_y = 20e3

        # md and flux lines attributes
        self.shift_fl_y = self.cross_len + 70e3
        self.shift_md_x = 175e3
        self.shift_md_y = 110e3

        self.cpwrl_md1: CPW_RL_Path = None
        self.cpwrl_md1_end: MDriveLineEnd = None
        self.cpwrl_fl1: CPW_RL_Path = None
        self.cpwrl_fl1_end: FluxLineEnd = None
        
        self.cpwrl_md2: CPW_RL_Path = None
        self.cpwrl_md2_end: MDriveLineEnd = None
        self.cpwrl_fl2: CPW_RL_Path = None
        self.cpwrl_fl2_end: FluxLineEnd = None
        
        self.cpwrl_md3: CPW_RL_Path = None
        self.cpwrl_md3_end: MDriveLineEnd = None
        self.cpwrl_fl3: CPW_RL_Path = None
        self.cpwrl_fl3_end: FluxLineEnd = None
        
        self.cpwrl_md4: CPW_RL_Path = None
        self.cpwrl_md4_end: MDriveLineEnd = None
        self.cpwrl_fl4: CPW_RL_Path = None
        self.cpwrl_fl4_end: FluxLineEnd = None
        
        self.cpwrl_md5: CPW_RL_Path = None
        self.cpwrl_md5_end: MDriveLineEnd = None
        self.cpwrl_fl5: CPW_RL_Path = None
        self.cpwrl_fl5_end: FluxLineEnd = None
        
        ### ADDITIONAL VARIABLES SECTION END ###

    def draw(self, design_params=None):
        self.draw_chip()
        self.draw_readout_waveguide()

        '''
            Only creating object. This is due to the drawing of xmons and resonators require
        draw xmons, then draw resonators and then draw additional xmons. This is
        ugly and that how this was before migrating to `ChipDesign` based code structure
            This is also the reason why `self.__init__` is flooded with design parameters that
        are used across multiple drawing functions.
        
        TODO: This drawings sequence can be decoupled in the future.
        '''
        self.create_resonator_objects()
        self.draw_xmons_and_resonators()
        self.draw_md_and_flux_lines()
        self.draw_josephson_loops()

        self.cell.shapes(self.layer_ph).insert(self.region_ph)
        self.cell.shapes(self.layer_el).insert(self.region_el)

    def draw_chip(self):
        chip_box = CHIP_10x10_12pads.box
        self.region_ph.insert(chip_box)

        self.contact_pads = CHIP_10x10_12pads.get_contact_pads()
        for contact_pad in self.contact_pads:
            contact_pad.place(self.region_ph)

    def draw_readout_waveguide(self):
        # place readout waveguide
        # place readout waveguide
        ro_line_turn_radius = self.ro_line_turn_radius
        ro_line_dy = self.ro_line_dy
        pcb_feedline_d = CHIP_10x10_12pads.pcb_feedline_d
        self.cpwrl_ro_line = CPW_RL_Path(
            self.contact_pads[-1].end, shape="LRLRLRLRL", cpw_parameters=self.Z0,
            turn_radiuses=[ro_line_turn_radius] * 4,
            segment_lengths=[ro_line_dy, pcb_feedline_d * 2 - pcb_feedline_d / 2 + 250e3 + 450e3,
                             ro_line_dy / 2, pcb_feedline_d / 2 + 250e3 + 450e3, ro_line_dy / 2],
            turn_angles=[pi / 2, pi / 2, pi / 2, -pi / 2], trans_in=Trans.R270
        )
        self.cpwrl_ro_line.place(self.region_ph)

    def create_resonator_objects(self):
        # fork at the end of resonator parameters
        fork_x_span = self.cross_width + 2 * (self.xmon_fork_gnd_gap + self.fork_metal_width)

        ### RESONATORS TAILS CALCULATIONS SECTION START ###
        # key to the calculations can be found in hand-written format here:
        # https://drive.google.com/file/d/1wFmv5YmHAMTqYyeGfiqz79a9kL1MtZHu/view?usp=sharing

        # distance between nearest resonators central conductors centers
        resonators_d = 400e3
        # x span between left long vertical line and
        # right-most center of central conductors
        resonators_widths = [2 * self.r + L_coupling for L_coupling in self.L_coupling_list]
        x1 = sum(resonators_widths[:2]) + 2 * resonators_d + resonators_widths[3] / 2 - 2 * self.xmon_x_distance
        x2 = x1 + self.xmon_x_distance - (resonators_widths[0] + resonators_d)
        x3 = sum(resonators_widths[:3]) + 3 * resonators_d - (x1 + 3 * self.xmon_x_distance)
        x4 = sum(resonators_widths[:4]) + 4 * resonators_d - (x1 + 4 * self.xmon_x_distance)

        res_tail_shape = "LRLRL"
        tail_turn_radiuses = self.r

        self.L2_list[0] += 6 * self.Z_res.b
        self.L2_list[1] += 0
        self.L2_list[3] += 3 * self.Z_res.b
        self.L2_list[4] += 6 * self.Z_res.b

        self.L4_list[1] += 6 * self.Z_res.b
        self.L4_list[2] += 6 * self.Z_res.b
        self.L4_list[3] += 3 * self.Z_res.b
        tail_segment_lengths_list = [
            [self.L2_list[0], x1, self.L4_list[0]],
            [self.L2_list[1], x2, self.L4_list[1]],
            [self.L2_list[2], (self.L_coupling_list[2] + 2 * self.r) / 2, self.L4_list[2]],
            [self.L2_list[3], x3, self.L4_list[3]],
            [self.L2_list[4], x4, self.L4_list[4]]
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
                self.L1_list, self.to_line_list, self.L_coupling_list,
                self.xmon_fork_penetration_list,
                tail_segment_lengths_list, tail_turn_angles_list, tail_trans_in_list
            )
        )
        for res_idx, params in enumerate(pars):
            # parameters exctraction
            L1 = params[0]
            to_line = params[1]
            L_coupling = params[2]
            xmon_fork_penetration = params[3]
            tail_segment_lengths = params[4]
            tail_turn_angles = params[5]
            tail_trans_in = params[6]

            # deduction for resonator placements
            # under condition that Xmon-Xmon distance equals
            # `xmon_x_distance`
            worm_x = 1.2 * CHIP_10x10_12pads.pcb_feedline_d + \
                     sum(resonators_widths[:res_idx]) + res_idx * resonators_d
            worm_y = self.contact_pads[-1].end.y - self.ro_line_dy - to_line
            # `fork_y_span` based on coupling modulated with
            # xmon_fork_penetration from `self.xmon_fork_penetration`
            fork_y_span = xmon_fork_penetration + self.xmon_fork_gnd_gap

            self.resonators.append(
                EMResonatorTL3QbitWormRLTailXmonFork(
                    self.Z_res, DPoint(worm_x, worm_y), L_coupling, self.L0, L1, self.r, self.N,
                    tail_shape=res_tail_shape, tail_turn_radiuses=tail_turn_radiuses,
                    tail_segment_lengths=tail_segment_lengths,
                    tail_turn_angles=tail_turn_angles, tail_trans_in=tail_trans_in,
                    fork_x_span=fork_x_span, fork_y_span=fork_y_span,
                    fork_metal_width=self.fork_metal_width, fork_gnd_gap=self.fork_gnd_gap
                )
            )

    def draw_xmons_and_resonators(self):
        for resonator, xmon_fork_penetration in zip(self.resonators, self.xmon_fork_penetration_list):
            xmon_center = (resonator.fork_y_cpw1.end + resonator.fork_y_cpw2.end) / 2
            xmon_center += DPoint(0, -(self.cross_len + self.cross_width / 2) + xmon_fork_penetration)
            self.xmons.append(
                XmonCross(xmon_center, self.cross_len_x, self.cross_width_x, self.cross_gnd_gap_x,
                          sideY_length=self.cross_len_y, sideY_width=self.cross_width_y,
                          sideY_gnd_gap=self.cross_gnd_gap_y)
            )
            self.xmons[-1].place(self.region_ph)
            resonator.place(self.region_ph)
            xmonCross_corrected = XmonCross(xmon_center, self.cross_len_x, self.cross_width_x, self.xmon_fork_gnd_gap,
                          sideY_length=self.cross_len_y, sideY_width=self.cross_width_y,
                          sideY_gnd_gap=self.xmon_fork_gnd_gap)
            xmonCross_corrected.place(self.region_ph)

    def draw_md_and_flux_lines(self):
        """
        Drawing of md (microwave drive) and flux tuning lines for 5 qubits
        Returns
        -------

        """
        contact_pads = self.contact_pads
        ctr_line_turn_radius = 200e3

        xmon_center = self.xmons[-1].center
        xmon_x_distance = self.xmon_x_distance
        cross_width_y = self.cross_width_y
        cross_width_x = self.cross_width_x
        cross_len_x = self.cross_len_x
        cross_gnd_gap_y = self.cross_gnd_gap_y
        cross_gnd_gap_x = self.cross_gnd_gap_x

        width_res = self.Z_res.width

        tmp_reg = self.region_ph
        Z_res = self.Z0

        shift_fl_y = self.cross_len + 70e3
        shift_md_x = 175e3
        shift_md_y = 110e3
        flux_end_width = 100e3

        # place caplanar line 1md
        self.cpwrl_md1 = CPW_RL_Path(
            contact_pads[0].end, shape="LRLRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius] * 3,
            segment_lengths=[2 * (-contact_pads[0].end.x + xmon_center.x - 4 * xmon_x_distance) / 16, (
                    (4 * (contact_pads[0].end.y - xmon_center.y) / 3) ** 2 + (11 * (
                    -contact_pads[0].end.x + xmon_center.x - 4 * xmon_x_distance) / 16) ** 2) ** 0.5 - 400e3, (
                                     ((contact_pads[0].end.y - xmon_center.y) / 3) ** 2 + ((-contact_pads[
                                 0].end.x + xmon_center.x - 4 * xmon_x_distance) / 16) ** 2) ** 0.5,
                             (-contact_pads[0].end.x + xmon_center.x - 4 * xmon_x_distance) / 16],
            turn_angles=[-atan2(4 * (contact_pads[0].end.y - xmon_center.y) / 3,
                                11 * (-contact_pads[0].end.x + xmon_center.x - 4 * xmon_x_distance) / 16), pi / 2,
                         -pi / 2 + atan2(4 * (contact_pads[0].end.y - xmon_center.y) / 3,
                                         11 * (-contact_pads[0].end.x + xmon_center.x - 4 * xmon_x_distance) / 16)],
            trans_in=Trans.R0
        )
        self.cpwrl_md1.place(tmp_reg)

        self.cpwrl_md1_end = MDriveLineEnd(self.cpwrl_md1.end, Z_res, width=14e3, trans_in=Trans.R270)
        self.cpwrl_md1_end.place(tmp_reg)

        # place caplanar line 1 fl
        self.cpwrl_fl1 = CPW_RL_Path(
            contact_pads[1].end, shape="LRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius],
            segment_lengths=[(-contact_pads[1].end.x + xmon_center.x - 4 * xmon_x_distance - cross_len_x), (
                    -contact_pads[1].end.y + xmon_center.y - cross_width_y / 2 - cross_gnd_gap_y - width_res)],
            turn_angles=[pi / 2], trans_in=Trans.R0
        )
        self.cpwrl_fl1.place(tmp_reg)

        self.cpwrl_fl1_end = FluxLineEnd(self.cpwrl_fl1.end, Z_res, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl1_end.place(tmp_reg)

        # place caplanar line 2md
        self.cpwrl_md2 = CPW_RL_Path(
            contact_pads[3].end, shape="LRLRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius] * 3,
            segment_lengths=[(-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 4,
                             (-contact_pads[3].end.x + xmon_center.x + shift_md_x - 3 * xmon_x_distance) / 2, (((-
                                                                                                                 contact_pads[
                                                                                                                     3].end.x + xmon_center.x + shift_md_x - 3 * xmon_x_distance) / 2) ** 2 + (
                                                                                                                       5 * (
                                                                                                                       -
                                                                                                                       contact_pads[
                                                                                                                           3].end.y + xmon_center.y - shift_md_y) / 8) ** 2) ** 0.5,
                             (-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 8],
            turn_angles=[-pi / 2, atan2(5 * (-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 8, (
                    -contact_pads[3].end.x + xmon_center.x + shift_md_x - 3 * xmon_x_distance) / 2),
                         pi / 2 - atan2(5 * (-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 8, (
                                 -contact_pads[3].end.x + xmon_center.x + shift_md_x - 3 * xmon_x_distance) / 2)],
            trans_in=Trans.R90
        )
        self.cpwrl_md2.place(tmp_reg)

        self.cpwrl_md2 = MDriveLineEnd(self.cpwrl_md2.end, Z_res, width=14e3, trans_in=Trans.R0)
        self.cpwrl_md2.place(tmp_reg)

        # place caplanar line 2 fl
        self.cpwrl_fl2 = CPW_RL_Path(
            contact_pads[2].end, shape="LRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius] * 2,
            segment_lengths=[(-contact_pads[2].end.x + xmon_center.x - 3 * xmon_x_distance) / 4, (
                    (3 * (-contact_pads[2].end.x + xmon_center.x - 3 * xmon_x_distance) / 4) ** 2 + (
                    7 * (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8) ** 2) ** 0.5,
                             (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8],
            turn_angles=[atan2(7 * (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8,
                               3 * (-contact_pads[2].end.x + xmon_center.x - 3 * xmon_x_distance) / 4),
                         pi / 2 - atan2(7 * (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8,
                                        3 * (-contact_pads[2].end.x + xmon_center.x - 3 * xmon_x_distance) / 4)],
            trans_in=Trans.R0
        )
        self.cpwrl_fl2.place(tmp_reg)

        self.cpwrl_fl2_end = FluxLineEnd(self.cpwrl_fl2.end, Z_res, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl2_end.place(tmp_reg)

        # place caplanar line 3md
        self.cpwrl_md3 = CPW_RL_Path(
            contact_pads[5].end, shape="LRLRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius] * 3,
            segment_lengths=[
                (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 4,
                (contact_pads[5].end.x - xmon_center.x - shift_md_x + 2 * xmon_x_distance) / 2,
                (
                        ((contact_pads[5].end.x - xmon_center.x - shift_md_x + 2 * xmon_x_distance) / 2) ** 2 +
                        (5 * (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8) ** 2) ** 0.5,
                (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8],
            turn_angles=[pi / 2, -atan2(5 * (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8,
                                        (contact_pads[5].end.x - xmon_center.x - shift_md_x + 2 * xmon_x_distance) / 2),
                         -pi / 2 + atan2(5 * (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8, (
                                 contact_pads[5].end.x - xmon_center.x - shift_md_x + 2 * xmon_x_distance) / 2)],
            trans_in=Trans.R90
        )
        self.cpwrl_md3.place(tmp_reg)

        self.cpwrl_md3_end = MDriveLineEnd(self.cpwrl_md3.end, Z_res, width=14e3, trans_in=Trans.R0)
        self.cpwrl_md3_end.place(tmp_reg)

        # place caplanar line 3 fl
        fl_l1 = (self.xmons[2].cpw_bempt.end.y - contact_pads[4].end.y)/4
        fl_l3 = fl_l1
        dr = self.xmons[2].cpw_bempt.end - contact_pads[4].end
        dr.y = dr.y - fl_l1 - fl_l3 - Z_res.width
        turn_angle = atan2(-dr.x, dr.y)
        fl_l2 = dr.abs()
        self.cpwrl_fl3 = CPW_RL_Path(
            self.contact_pads[4].end, shape="LRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius]*2,
            segment_lengths=[fl_l1, fl_l2, fl_l3],
            turn_angles=[turn_angle, -turn_angle], trans_in=Trans.R90
        )
        self.cpwrl_fl3.place(tmp_reg)

        self.cpwrl_fl3_end = FluxLineEnd(self.cpwrl_fl3.end, Z_res, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl3_end.place(tmp_reg)

        # place caplanar line 4 md
        self.cpwrl_md4 = CPW_RL_Path(
            contact_pads[7].end, shape="LRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius],
            segment_lengths=[contact_pads[7].end.x - xmon_center.x + xmon_x_distance - shift_md_x,
                             -contact_pads[7].end.y + xmon_center.y - shift_md_y],
            turn_angles=[-pi / 2], trans_in=Trans.R180
        )
        self.cpwrl_md4.place(tmp_reg)

        self.cpwrl_md4_end = MDriveLineEnd(self.cpwrl_md4.end, Z_res, width=14e3, trans_in=Trans.R0)
        self.cpwrl_md4_end.place(tmp_reg)

        # place caplanar line 4 fl
        self.cpwrl_fl4 = CPW_RL_Path(
            contact_pads[6].end, shape="LRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius] * 2,
            segment_lengths=[(contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4,
                             ((7 * (-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8) ** 2 +
                              (3 * (contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4) ** 2) ** 0.5,
                             (-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8],
            turn_angles=[-atan2(7 * (-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8,
                                3 * (contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4),
                         -pi / 2 + atan2(7 * (-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8,
                                         3 * (contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4)],
            trans_in=Trans.R180
        )
        self.cpwrl_fl4.place(tmp_reg)

        self.cpwrl_fl4_end = FluxLineEnd(self.cpwrl_fl4.end, Z_res, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl4_end.place(tmp_reg)

        # place caplanar line 5 md
        self.cpwrl_md5 = CPW_RL_Path(
            contact_pads[9].end, shape="LRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius] * 2,
            segment_lengths=[
                2 * (contact_pads[9].end.y - xmon_center.y) / 3 - cross_gnd_gap_y - cross_width_y - 20e3,
                (
                        ((contact_pads[9].end.y - xmon_center.y) / 3) ** 2 +
                        (
                                2 * (contact_pads[9].end.x - xmon_center.x - cross_len_x -
                                     cross_width_x / 2 - cross_gnd_gap_x) / 3
                        )**2
                )**(0.5),
                (contact_pads[9].end.x - xmon_center.x - cross_len_x - cross_width_x / 2 - cross_gnd_gap_x) / 3 + 30e3
            ],
            turn_angles=[-atan2(
                2 * (contact_pads[9].end.x - xmon_center.x - cross_len_x - cross_width_x / 2 - cross_gnd_gap_x) / 3,
                (contact_pads[9].end.y - xmon_center.y) / 3), atan2(
                2 * (contact_pads[9].end.x - xmon_center.x - cross_len_x - cross_width_x / 2 - cross_gnd_gap_x) / 3,
                (contact_pads[9].end.y - xmon_center.y) / 3) - pi / 2], trans_in=Trans.R270
        )
        self.cpwrl_md5.place(tmp_reg)

        self.cpwrl_md5_end = MDriveLineEnd(self.cpwrl_md5.end, Z_res, width=14e3, trans_in=Trans.R90)
        self.cpwrl_md5_end.place(tmp_reg)

        # place caplanar line 5 fl
        self.cpwrl_fl5 = CPW_RL_Path(
            contact_pads[8].end, shape="LRLRLRLRL", cpw_parameters=Z_res,
            turn_radiuses=[ctr_line_turn_radius] * 4,
            segment_lengths=[(contact_pads[8].end.x - xmon_center.x) / 4,
                             ((contact_pads[8].end.y - xmon_center.y) + 250e3) / 3 + 50e3, (
                                     (2 * ((contact_pads[8].end.y - xmon_center.y) + 250e3) / 3) ** 2 + (
                                     (contact_pads[8].end.x - xmon_center.x) / 2) ** 2) ** 0.5,
                             (contact_pads[8].end.x - xmon_center.x) / 4 - cross_len_x, 230e3],
            turn_angles=[pi / 2, -atan2((contact_pads[8].end.x - xmon_center.x) / 2,
                                        2 * ((contact_pads[8].end.y - xmon_center.y) + 250e3) / 3),
                         - pi / 2 + atan2((contact_pads[8].end.x - xmon_center.x) / 2,
                                          2 * ((contact_pads[8].end.y - xmon_center.y) + 250e3) / 3), -pi / 2],
            trans_in=Trans.R180
        )
        self.cpwrl_fl5.place(tmp_reg)

        self.cpwrl_fl5_end = FluxLineEnd(self.cpwrl_fl5.end, Z_res, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl5_end.place(tmp_reg)

    def draw_josephson_loops(self):
        new_pars_squid = AsymSquidParams(
            pad_r=5e3, pads_distance=30e3,
            p_ext_width=5e3, p_ext_r=200,
            sq_len=7e3, sq_area=35e6,
            j_width_1=94, j_width_2=347,
            intermediate_width=500, b_ext=1e3, j_length=94, n=20,
            bridge=180, j_length_2=250
        )
        # place left squid
        xmon0 = self.xmons[0]
        center1 = DPoint(
            self.cpwrl_fl1_end.end.x,
            xmon0.center.y - (xmon0.sideX_width + xmon0.sideX_gnd_gap)/2
        )
        squid = AsymSquid(center1, new_pars_squid, 0)
        squid.place(self.region_el)
        print(self.cpwrl_fl1_end.end)

        # place intermediate squids
        for xmon_cross in self.xmons[1:-1]:
            squid_center = (xmon_cross.cpw_bempt.start + xmon_cross.cpw_bempt.end) / 2
            squid = AsymSquid(squid_center, new_pars_squid, 0)
            squid.place(self.region_el)

        # place right squid
        xmon5 = self.xmons[4]
        center5 = DPoint(
            self.cpwrl_fl5_end.end.x,
            xmon5.center.y - (xmon5.sideX_width + xmon5.sideX_gnd_gap) / 2
        )
        squid = AsymSquid(center5, new_pars_squid, 0)
        squid.place(self.region_el)




if __name__ == "__main__":
    design = Design5Q("testCell")
    design.draw()
    design.lv.zoom_fit()
