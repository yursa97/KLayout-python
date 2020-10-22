# Enter your Python code here
from math import cos, sin, atan2, pi
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
import сlassLib
reload(сlassLib)

from сlassLib.coplanars import CPWParameters, CPW_RL_Path
from сlassLib.shapes import XmonCross
from сlassLib.resonators import EMResonatorTL3QbitWormRLTailXmonFork
from сlassLib.chipTemplates import CHIP_10x10_12pads
from сlassLib.chipDesign import ChipDesign

# imports for docstrings generation
from typing import List, Dict
from сlassLib.contactPads import ContactPad


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
        self.ro_line_turn_radius: float = None
        self.ro_line_dy: float = None
        self.cpw_ro_line: CPW_RL_Path = None

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
        self.cross_len: float = 125e3
        self.cross_gnd_gap: float = 20e3
        self.xmon_x_distance: float = 393e3  # from simulation of g_12
        self.xmons: list[XmonCross] = []
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

        self.cell.shapes(self.layer_ph).insert(self.region_ph)
        pass

    def draw_chip(self):
        chip_box = CHIP_10x10_12pads.box
        self.region_ph.insert(chip_box)

        self.contact_pads = CHIP_10x10_12pads.get_contact_pads()
        for contact_pad in self.contact_pads:
            contact_pad.place(self.region_ph)

    def draw_readout_waveguide(self):
        # place readout waveguide
        self.ro_line_turn_radius = 200e3
        self.ro_line_dy = 600e3
        Z0 = CPWParameters(CHIP_10x10_12pads.cpw_width, CHIP_10x10_12pads.cpw_gap)
        self.cpw_ro_line = CPW_RL_Path(
            self.contact_pads[-1].end, shape="LRLRL", cpw_parameters=Z0,
            turn_radiuses=[self.ro_line_turn_radius] * 2,
            segment_lengths=[self.ro_line_dy, CHIP_10x10_12pads.pcb_feedline_d, self.ro_line_dy],
            turn_angles=[pi / 2, pi / 2], trans_in=Trans.R270
        )
        self.cpw_ro_line.place(self.region_ph)

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
                XmonCross(xmon_center, self.cross_width, self.cross_len, self.cross_gnd_gap)
            )
            self.xmons[-1].place(self.region_ph)
            resonator.place(self.region_ph)
            xmonCross_corrected = XmonCross(xmon_center, self.cross_width, self.cross_len, self.xmon_fork_gnd_gap)
            xmonCross_corrected.place(self.region_ph)


if __name__ == "__main__":
    design = Design5Q("testCell")
    design.draw()
    design.lv.zoom_fit()