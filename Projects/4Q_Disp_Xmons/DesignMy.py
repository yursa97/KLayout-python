# Enter your Python code here
from math import cos, sin, tan, atan2, pi, degrees
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
import classLib

reload(classLib)

from classLib.baseClasses import ElementBase, ComplexBase
from classLib.coplanars import CPWParameters, CPW_RL_Path, CPW2CPW
from classLib.shapes import XmonCross
from classLib.resonators import EMResonatorTL3QbitWormRLTailXmonFork
from classLib.josJ import AsymSquidParams, AsymSquid
from classLib.chipTemplates import CHIP_10x10_12pads
from classLib.chipDesign import ChipDesign

# imports for docstrings generation
from classLib.coplanars import CPW, CPW_arc
from typing import List, Dict, Union
from classLib.contactPads import ContactPad

class FluxLineEnd(ElementBase):

    def __init__(self, origin, fc_cpw_params, width, trans_in=None):  

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


class MDriveLineEnd(ComplexBase):

    def __init__(self, z0_cpw, z1_cpw_params, transition_length, z1_length, trans_in=None):
        """
        Makes transition to thin Z at the end of the md coplanar.

        Parameters
        ----------
        z0_cpw : Union[CPW, CPW_arc]
            last part of the md coplanar
        z1_cpw_params : Union[CPWParameters, CPW]
            parameters of the thin coplanar
        transition_length : float
            length of cpw2cpw transition
        z1_length : float
            length of the z1 thin coplanar
        trans_in : DCplxTrans
            initial transformation
        """
        self.z0_cpw: Union[CPW, CPW_arc] = z0_cpw
        self.z1_params: Union[CPWParameters, CPW] = z1_cpw_params
        self.transition_length: float = transition_length
        self.z1_length: float = z1_length

        # attributes to be constructed later
        self.transition_cpw2cpw: CPW2CPW = None
        self.z1_cpw: CPW = None
        self.z1_cpw_open_end: CPW = None

        super().__init__(self.z0_cpw.end, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]

    def init_primitives(self):
        origin = DPoint(0, 0)
        transition_end = origin + DPoint(self.transition_length, 0)
        alpha = self.z0_cpw.angle_connections[1]

        self.transition_cpw2cpw = CPW2CPW(
            self.z0_cpw, self.z1_params, origin, transition_end,
            trans_in=DCplxTrans(1, degrees(alpha), False, 0, 0)
        )
        self.primitives["transition_cpw2cpw"] = self.transition_cpw2cpw

        z1_cpw_end = self.transition_cpw2cpw.end + DPoint(self.z1_length, 0)
        self.z1_cpw = CPW(cpw_params=self.z1_params,
                          start=self.transition_cpw2cpw.end, end=z1_cpw_end,
                          trans_in=DCplxTrans(1, degrees(alpha), False, 0, 0))
        self.primitives["z1_cpw"] = self.z1_cpw

        # open-ended
        self.z1_cpw_open_end = CPW(
            0, gap=self.z1_params.b/2,
            start=self.z1_cpw.end, end=self.z1_cpw.end + DPoint(self.z1_params.b/2, 0),
            trans_in=DCplxTrans(1, degrees(alpha), False, 0, 0)
        )
        self.primitives["z1_cpw_open_end"] = self.z1_cpw_open_end

        self.connections = [self.transition_cpw2cpw.start, self.z1_cpw.end]
        x = self.z1_params.b/2


class EMResonator_TL2Qbit_worm3(ComplexBase):
    def __init__(self, Z0, start, L_coupling, L0, L1, r, L2, N, trans_in=None):
        self.Z0 = Z0
        self.L_coupling = L_coupling
        self.L0 = L0
        self.L1 = L1
        self.r = r
        self.L2 = L2
        self.N = N

        super().__init__(start, trans_in)

        self._geometry_parameters["cpw_width, um"] = Z0.width
        self._geometry_parameters["cpw_gap, um"] = Z0.gap
        self._geometry_parameters["L_coupling, um"] = L_coupling
        self._geometry_parameters["L0, um"] = L0
        self._geometry_parameters["L1, um"] = L1
        self._geometry_parameters["r, um"] = r
        self._geometry_parameters["L2, um"] = L2
        self._geometry_parameters["N"] = N

        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

    def init_primitives(self):
        # making coil
        name = "coil0"
        setattr(self, name, Coil_type_1(self.Z0, DPoint(0, 0), self.L_coupling, self.r, self.L1))
        self.primitives[name] = getattr(self, name)
        # coils filling
        for i in range(self.N):
            name = "coil" + str(i + 1)
            setattr(self, name,
                    Coil_type_1(self.Z0, DPoint(-self.L1 + self.L_coupling, -(i + 1) * (4 * self.r)), self.L1, self.r,
                                self.L1))
            self.primitives[name] = getattr(self, name)

        # draw the "tail"
        self.arc_tail = CPW_arc(self.Z0, self.primitives["coil" + str(self.N)].end, -self.L1 / 2, -pi / 2)
        self.cop_tail = CPW(self.Z0.width, self.Z0.gap, self.arc_tail.end, self.arc_tail.end - DPoint(0, self.L2))
        
        self.arc_tail_1 = CPW_arc(self.Z0, DPoint(0,0), self.L1 / 2, -pi/2)
        self.cop_tail_1 = CPW(self.Z0.width, self.Z0.gap, self.arc_tail_1.end, self.arc_tail_1.end - DPoint(0, -self.L2))

        # tail face is separated from ground by `b = width + 2*gap`
        self.cop_open_end = CPW(0, self.Z0.b / 2, self.cop_tail.end, self.cop_tail.end - DPoint(0, self.Z0.b))
        self.primitives["arc_tail"] = self.arc_tail
        self.primitives["cop_tail"] = self.cop_tail
        self.primitives["arc_tail_1"] = self.arc_tail_1
        self.primitives["cop_tail_1"] = self.cop_tail_1
        self.primitives["cop_open_end"] = self.cop_open_end

        self.connections = [DPoint(0, 0), self.cop_tail.end]
        self.angle_connections = [0, self.cop_tail.alpha_end]


class EMResonator_TL2Qbit_worm4_XmonFork(EMResonator_TL2Qbit_worm3):
    def __init__(self, Z0, start, L_coupling, L0, L1, r, L2, N,
                 fork_x_span, fork_metal_width, fork_gnd_gap,
                 trans_in=None):
        self.fork_x_span = fork_x_span
        self.fork_metal_width = fork_metal_width
        self.fork_gnd_gap = fork_gnd_gap

        super().__init__(
            Z0, start, L_coupling, L0, L1, r, L2, N, trans_in
        )

        self._geometry_parameters["fork_x_span, um"] = fork_x_span / 1e3
        self._geometry_parameters["fork_metal_width, um"] = fork_metal_width / 1e3
        self._geometry_parameters["fork_gnd_gap, um"] = fork_gnd_gap / 1e3

    def init_primitives(self):
        super().init_primitives()

        """ add fork to the end of the resonator """
        # remove open end from the resonator
        del self.primitives["cop_open_end"]
        del self.cop_open_end

        # adding fork horizontal part
        self.draw_fork_along_x()

    def draw_fork_along_x(self):
        forkZ = CPW(self.fork_metal_width, self.fork_gnd_gap)
        p1 = self.cop_tail.end + DPoint(-self.fork_x_span / 2, - forkZ.b / 2)
        p2 = p1 + DPoint(self.fork_x_span, 0)
        self.fork_x_cpw = CPW(forkZ.width, forkZ.gap, p1, p2)
        self.primitives["fork_x_cpw"] = self.fork_x_cpw

        # return waveguide that was erased during ground drawing
        p3 = self.cop_tail.end + DPoint(0, -forkZ.gap)
        erased_cpw = CPW(self.Z0.width, self.Z0.gap, self.cop_tail.end, p3)
        self.primitives["erased_cpw"] = erased_cpw

        # erase additional spaces at the ends of fork_x_cpw
        p1 = self.fork_x_cpw.start + DPoint(-forkZ.gap, 0)
        self.primitives["erased_fork_left"] = CPW(0, forkZ.b / 2, self.fork_x_cpw.start, p1)
        p1 = self.fork_x_cpw.end + DPoint(forkZ.gap, 0)
        self.primitives["erased_fork_right"] = CPW(0, forkZ.b / 2, self.fork_x_cpw.end, p1)



# horisntal part 2

        self.draw_fork_along_x_new()

    def draw_fork_along_x_new(self):
        forkZ_new = CPW(self.fork_metal_width, self.fork_gnd_gap)
        p1 = self.cop_tail_1.end + DPoint(-self.fork_x_span / 2,  forkZ_new.b / 2)
        p2 = p1 + DPoint(self.fork_x_span, 0)
        self.fork_x_cpw_new = CPW(forkZ_new.width, forkZ_new.gap, p1, p2)
        self.primitives["fork_x_cpw_new"] = self.fork_x_cpw_new

        # return waveguide that was erased during ground drawing
        p3 = self.cop_tail_1.end + DPoint(0, forkZ_new.gap)
        erased_cpw_new = CPW(self.Z0.width, self.Z0.gap, self.cop_tail_1.end, p3)
        self.primitives["erased_cpw_new"] = erased_cpw_new

        # erase additional spaces at the ends of fork_x_cpw
        p1 = self.fork_x_cpw_new.start + DPoint(-forkZ_new.gap, 0)
        self.primitives["erased_fork_left_new"] = CPW(0, forkZ_new.b / 2, self.fork_x_cpw_new.start, p1)
        p1 = self.fork_x_cpw_new.end + DPoint(forkZ_new.gap, 0)
        self.primitives["erased_fork_right_new"] = CPW(0, forkZ_new.b / 2, self.fork_x_cpw_new.end, p1)



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
        self.L_coupling_list1 = [1e3 * x for x in [255, 250]]
        self.L_coupling_list2 = [1e3 * x for x in [ 240, 230]]
        # corresponding to resonanse freq is linspaced in interval [6,9) GHz
        self.L0 = 1600e3
        self.L1_list1 = [1e3 * x for x in [37.7039, 67.6553]]
        self.L1_list2 = [1e3 * x for x in [81.5881, 39.9021]]
        self.r = 60e3
        self.N = 5
        self.L2_list1 = [self.r] * len(self.L1_list1)
        self.L4_list1 = [self.r] * len(self.L1_list1)
        self.L2_list2 = [self.r] * len(self.L1_list2)
        self.L4_list2 = [self.r] * len(self.L1_list2)
        self.width_res = 20e3
        self.gap_res = 10e3
        self.Z_res = CPWParameters(self.width_res, self.gap_res)
        self.to_line_list = [53e3] * len(self.L1_list1)
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
        self.xmon_x_distance: float = 485e3  # from simulation of g_12
        self.xmons1: list[XmonCross] = []
        self.xmons2: list[XmonCross] = []

        self.cross_len_x = 180e3
        self.cross_width_x = 60e3
        self.cross_width_y = 60e3
        self.cross_len_y = 60e3
        self.cross_gnd_gap_x = 20e3
        self.cross_gnd_gap_y = 20e3
        
        self.worm:EMResonator_TL2Qbit_worm4_XmonFork = None

        # md and flux lines attributes
        self.shift_fl_y = self.cross_len + 70e3
        self.shift_md_x = 175e3
        self.shift_md_y = 200e3

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
        self.create_resonator_objects1()
        self.create_resonator_objects2()
        self.draw_xmons_and_resonators1()
        self.draw_xmons_and_resonators2()
        self.draw_common_resonator()
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
            self.contact_pads[-1].end, shape="LRLRL", cpw_parameters=self.Z0,
            turn_radiuses=[ro_line_turn_radius] * 2,
            segment_lengths=[ro_line_dy, pcb_feedline_d * 2, ro_line_dy],
            turn_angles=[pi / 2, pi / 2], trans_in=Trans.R270
        )
        self.cpwrl_ro_line.place(self.region_ph)

    def create_resonator_objects1(self):
        # fork at the end of resonator parameters
        fork_x_span = self.cross_width + 2 * (self.xmon_fork_gnd_gap + self.fork_metal_width)

        ### RESONATORS TAILS CALCULATIONS SECTION START ###
        # key to the calculations can be found in hand-written format here:
        # https://drive.google.com/file/d/1wFmv5YmHAMTqYyeGfiqz79a9kL1MtZHu/view?usp=sharing

        # distance between nearest resonators central conductors centers
        resonators_d = 420e3
        # x span between left long vertical line and
        # right-most center of central conductors
        resonators_widths = [2 * self.r + L_coupling for L_coupling in self.L_coupling_list1]
        x1 = sum(resonators_widths) + 2 * resonators_d + resonators_widths[1] / 2 - 2 * self.xmon_x_distance -350e3
        x2 = x1 + self.xmon_x_distance - (resonators_widths[0] + resonators_d)


        res_tail_shape = "LRLRL"
        tail_turn_radiuses = self.r

        self.L2_list1[0] += 6 * self.Z_res.b
        self.L2_list1[1] += 0

#
        self.L4_list1[1] += 6 * self.Z_res.b

        tail_segment_lengths_list = [
            [self.L2_list1[0], x1, self.L4_list1[0]],
            [self.L2_list1[1], x2, self.L4_list1[1]],

        ]
        tail_turn_angles_list = [
            [pi / 2, -pi / 2],
            [pi / 2, -pi / 2],

        ]
        tail_trans_in_list = [
            Trans.R270,
            Trans.R270,
        ]
        ### RESONATORS TAILS CALCULATIONS SECTION END ###

        pars = list(
            zip(
                self.L1_list1, self.to_line_list, self.L_coupling_list1,
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
                     sum(resonators_widths[:res_idx]) + res_idx * resonators_d - 150e3
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

    def draw_xmons_and_resonators1(self):
        for resonator, xmon_fork_penetration in zip(self.resonators, self.xmon_fork_penetration_list):
            xmon_center = (resonator.fork_y_cpw1.end + resonator.fork_y_cpw2.end) / 2
            xmon_center += DPoint(0, -(self.cross_len + self.cross_width / 2) + xmon_fork_penetration)
            self.xmons1.append(
                XmonCross(xmon_center, self.cross_len_x, self.cross_width_x, self.cross_gnd_gap_x,
                          sideY_length=self.cross_len_y, sideY_width=self.cross_width_y,
                          sideY_gnd_gap=self.cross_gnd_gap_y)
            )
            self.xmons1[-1].place(self.region_ph)
            resonator.place(self.region_ph)
            xmonCross_corrected = XmonCross(xmon_center, self.cross_len_x, self.cross_width_x, self.xmon_fork_gnd_gap,
                          sideY_length=self.cross_len_y, sideY_width=self.cross_width_y,
                          sideY_gnd_gap=self.xmon_fork_gnd_gap)
            xmonCross_corrected.place(self.region_ph)
            

# try second pair
            
    def create_resonator_objects2(self):
        # fork at the end of resonator parameters
        fork_x_span = self.cross_width + 2 * (self.xmon_fork_gnd_gap + self.fork_metal_width)

        ### RESONATORS TAILS CALCULATIONS SECTION START ###
        # key to the calculations can be found in hand-written format here:
        # https://drive.google.com/file/d/1wFmv5YmHAMTqYyeGfiqz79a9kL1MtZHu/view?usp=sharing

        # distance between nearest resonators central conductors centers
        resonators_d = 420e3
        # x span between left long vertical line and
        # right-most center of central conductors
        resonators_widths = [2 * self.r + L_coupling for L_coupling in self.L_coupling_list2]
#        x1 = sum(resonators_widths) + 2 * resonators_d + resonators_widths[1] / 2 - 2 * self.xmon_x_distance -350e3
        x1 =  resonators_d/2 - 50e3  
        x2 = x1 + 0.61*self.xmon_x_distance - 1e3


        res_tail_shape = "LRLRL"
        tail_turn_radiuses = self.r

        self.L2_list2[0] += 0 * self.Z_res.b
        self.L2_list2[1] +=3 * self.Z_res.b
     
        self.L4_list2[0] += 6 * self.Z_res.b
        self.L4_list2[1] += 3 * self.Z_res.b

        tail_segment_lengths_list = [
            [self.L2_list2[0], x1, self.L4_list2[0]],
            [self.L2_list2[1], x2, self.L4_list2[1]],
        ]
        tail_turn_angles_list = [
            [-pi / 2, pi / 2],
            [-pi / 2, pi / 2],
        ]
        tail_trans_in_list = [
            Trans.R270,
            Trans.R270
        ]
        ### RESONATORS TAILS CALCULATIONS SECTION END ###

        pars = list(
            zip(
                self.L1_list2, self.to_line_list, self.L_coupling_list2,
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
            worm_x = 2 * CHIP_10x10_12pads.pcb_feedline_d + \
                     sum(resonators_widths[:res_idx]) + res_idx * resonators_d + 1135e3
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

    def draw_xmons_and_resonators2(self):
        for resonator, xmon_fork_penetration in zip(self.resonators, self.xmon_fork_penetration_list):
            xmon_center = (resonator.fork_y_cpw1.end + resonator.fork_y_cpw2.end) / 2
            xmon_center += DPoint(0, -(self.cross_len + self.cross_width / 2) + xmon_fork_penetration)
            self.xmons2.append(
                XmonCross(xmon_center, self.cross_len_x, self.cross_width_x, self.cross_gnd_gap_x,
                          sideY_length=self.cross_len_y, sideY_width=self.cross_width_y,
                          sideY_gnd_gap=self.cross_gnd_gap_y)
            )
            self.xmons2[-1].place(self.region_ph)
            resonator.place(self.region_ph)
            xmonCross_corrected = XmonCross(xmon_center, self.cross_len_x, self.cross_width_x, self.xmon_fork_gnd_gap,
                          sideY_length=self.cross_len_y, sideY_width=self.cross_width_y,
                          sideY_gnd_gap=self.xmon_fork_gnd_gap)
            xmonCross_corrected.place(self.region_ph)

    def draw_common_resonator(self):
      # fork at the end of resonator parameters
      fork_metal_width = 20e3
      fork_gnd_gap = 20e3
      xmon_fork_gnd_gap = 20e3
      fork_x_span = cross_width + 2 * (xmon_fork_gnd_gap + fork_metal_width)
      self.worm = EMResonator_TL2Qbit_worm4_XmonFork(Z_res, DPoint(5e6+400e3 - 30e3 + 50e3,5e6+400e3 - 23e3), 0, 0,200e3, r, 100e3, 5,fork_x_span, fork_metal_width, fork_gnd_gap, Trans.R270)
        
      self.worm.place(self.region_ph)      
    def draw_md_and_flux_lines(self):          
#    def draw_md_and_flux_lines(self):
        """
        Drawing of md (microwave drive) and flux tuning lines for 4 qubits
        Returns
        -------

        """
        contact_pads = self.contact_pads
        ctr_line_turn_radius = 200e3

        xmon_center1 = self.xmons1[-1].center
        xmon_center = self.xmons2[-1].center
        xmon_x_distance = self.xmon_x_distance
        cross_width_y = self.cross_width_y
        cross_width_x = self.cross_width_x
        cross_len_x = self.cross_len_x
        cross_gnd_gap_y = self.cross_gnd_gap_y
        cross_gnd_gap_x = self.cross_gnd_gap_x

        width_res = self.Z_res.width

        tmp_reg = self.region_ph
        z_md_fl = self.Z0

        shift_fl_y = self.cross_len + 70e3
        shift_md_x = 150e3
        shift_md_y = 360e3
        flux_end_width = 100e3
        common_res = 1730e3 - 25e3

        md_transition = 25e3
        md_z1_params = CPWParameters(7e3, 4e3)  # Z = 50.04 Ohm, E_eff = 6.237 (E_0 = 11.45)     (8e3, 4.15e3)
        md_z1_length = 100e3
        shift_md_x_side = md_z1_length + md_transition + md_z1_params.b/2 + cross_len_x + cross_width_x / 2 + cross_gnd_gap_x

        # place caplanar line 1md
        self.cpwrl_md1 = CPW_RL_Path(
            contact_pads[0].end, shape="LRLRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius] * 2,
            segment_lengths=[2 * (-contact_pads[0].end.x + xmon_center1.x - 3 * xmon_x_distance - common_res -  shift_md_x_side) / 16, (
                    (contact_pads[0].end.y - xmon_center1.y) ** 2 + (9 * (
                    -contact_pads[0].end.x + xmon_center1.x - 3 * xmon_x_distance - common_res -  shift_md_x_side) / 16) ** 2) ** 0.5,
                            5 * (-contact_pads[0].end.x + xmon_center1.x - 3 * xmon_x_distance - common_res -  shift_md_x_side) / 16 - 140e3],
            turn_angles=[-atan2(contact_pads[0].end.y - xmon_center1.y,
                                9 * (-contact_pads[0].end.x + xmon_center1.x - 3 * xmon_x_distance - common_res -  shift_md_x_side) / 16), 
                         atan2(contact_pads[0].end.y - xmon_center1.y,
                                9 * (-contact_pads[0].end.x + xmon_center1.x - 3 * xmon_x_distance - common_res -  shift_md_x_side) / 16)],
            trans_in=Trans.R0
        )
        self.cpwrl_md1.place(tmp_reg)

        self.cpwrl_md1_end = MDriveLineEnd(list(self.cpwrl_md1.primitives.values())[-1], md_z1_params, md_transition, md_z1_length)
        self.cpwrl_md1_end.place(tmp_reg)

        # place caplanar line 1 fl
        self.cpwrl_fl1 = CPW_RL_Path(
            contact_pads[1].end, shape="LRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius],
            segment_lengths=[(-contact_pads[1].end.x + xmon_center1.x - 3* xmon_x_distance - common_res), (
                    -contact_pads[1].end.y + xmon_center1.y - shift_fl_y)],
            turn_angles=[pi / 2], trans_in=Trans.R0
        )
        self.cpwrl_fl1.place(tmp_reg)

        self.cpwrl_fl1_end = FluxLineEnd(self.cpwrl_fl1.end, z_md_fl, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl1_end.place(tmp_reg)
        
        # place caplanar line 2md
        self.cpwrl_md2 = CPW_RL_Path(
            contact_pads[3].end, shape="LRLRLRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius] * 3,
            segment_lengths=[(-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 4,
                             (-contact_pads[3].end.x + xmon_center.x + shift_md_x - 2 * xmon_x_distance - common_res) / 2, (((-
                                                                                                                 contact_pads[
                                                                                                                     3].end.x + xmon_center.x + shift_md_x - 2 * xmon_x_distance - common_res) / 2) ** 2 + (
                                                                                                                       5 * (
                                                                                                                       -
                                                                                                                       contact_pads[
                                                                                                                           3].end.y + xmon_center.y - shift_md_y) / 8) ** 2) ** 0.5,
                             (-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 8],
            turn_angles=[-pi / 2, atan2(5 * (-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 8, (
                    -contact_pads[3].end.x + xmon_center.x + shift_md_x - 2 * xmon_x_distance - common_res) / 2),
                         pi / 2 - atan2(5 * (-contact_pads[3].end.y + xmon_center.y - shift_md_y) / 8, (
                                 -contact_pads[3].end.x + xmon_center.x + shift_md_x - 2 * xmon_x_distance - common_res) / 2)],
            trans_in=Trans.R90
        )
        self.cpwrl_md2.place(tmp_reg)

        self.cpwrl_md2 = MDriveLineEnd(
            list(self.cpwrl_md2.primitives.values())[-1],
            md_z1_params, md_transition, md_z1_length
        )
        self.cpwrl_md2.place(tmp_reg)
        
      # place caplanar line 2 fl
      
        self.cpwrl_fl2 = CPW_RL_Path(
            contact_pads[2].end, shape="LRLRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius] * 2,
            segment_lengths=[(-contact_pads[2].end.x + xmon_center.x - 2 * xmon_x_distance - common_res) / 4, (
                    (3 * (-contact_pads[2].end.x + xmon_center.x - 2 * xmon_x_distance - common_res) / 4) ** 2 + (
                    7 * (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8) ** 2) ** 0.5,
                             (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8],
            turn_angles=[atan2(7 * (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8,
                               3 * (-contact_pads[2].end.x + xmon_center.x - 2 * xmon_x_distance - common_res) / 4),
                         pi / 2 - atan2(7 * (-contact_pads[2].end.y + xmon_center.y - shift_fl_y) / 8,
                                        3 * (-contact_pads[2].end.x + xmon_center.x - 2 * xmon_x_distance - common_res) / 4)],
            trans_in=Trans.R0
        )
        self.cpwrl_fl2.place(tmp_reg)

        self.cpwrl_fl2_end = FluxLineEnd(self.cpwrl_fl2.end, z_md_fl, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl2_end.place(tmp_reg)


        # place caplanar line 3md
        self.cpwrl_md3 = CPW_RL_Path(
            contact_pads[5].end, shape="LRLRLRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius] * 3,
            segment_lengths=[
                (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 4,
                (contact_pads[5].end.x - xmon_center.x - shift_md_x +  xmon_x_distance) / 2+300e3,
                (
                        ((contact_pads[5].end.x - xmon_center.x - shift_md_x +  xmon_x_distance) / 2) ** 2 +
                        (5 * (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8) ** 2) ** 0.5,
                (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8],
            turn_angles=[pi / 2, -atan2(5 * (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8,
                                        (contact_pads[5].end.x - xmon_center.x - shift_md_x +  xmon_x_distance) / 2),
                         -pi / 2 + atan2(5 * (-contact_pads[5].end.y + xmon_center.y - shift_md_y) / 8, (
                                 contact_pads[5].end.x - xmon_center.x - shift_md_x +  xmon_x_distance) / 2)],
            trans_in=Trans.R90
        )
        self.cpwrl_md3.place(tmp_reg)

        self.cpwrl_md3_end = MDriveLineEnd(
            list(self.cpwrl_md3.primitives.values())[-1], md_z1_params, md_transition, md_z1_length
        )
        self.cpwrl_md3_end.place(tmp_reg)

        # place caplanar line 3 fl
        self.cpwrl_fl4 = CPW_RL_Path(
            contact_pads[6].end, shape="LRLRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius] * 2,
            segment_lengths=[(contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4,
                             ((7 * (-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8) ** 2 +
                              (3 * (contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4) ** 2) ** 0.5,
                             1*(-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8],
            turn_angles=[-atan2(7 * (-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8,
                                3 * (contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4),
                         -pi / 2 + atan2(7 * (-contact_pads[6].end.y + xmon_center.y - shift_fl_y) / 8,
                                         3 * (contact_pads[6].end.x - xmon_center.x + xmon_x_distance) / 4)],
            trans_in=Trans.R180
        )
        self.cpwrl_fl4.place(tmp_reg)

        self.cpwrl_fl4_end = FluxLineEnd(self.cpwrl_fl4.end, z_md_fl, width=flux_end_width, trans_in=Trans.R0)
        self.cpwrl_fl4_end.place(tmp_reg)

        # place caplanar line 4 md
        
        self.cpwrl_md5 = CPW_RL_Path(
            contact_pads[8].end, shape="LRLRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius] * 2,
            segment_lengths=[2 * (contact_pads[8].end.x - xmon_center1.x  -  shift_md_x_side) / 16, (
                    (contact_pads[8].end.y - xmon_center1.y) ** 2 + (9 * (
                    contact_pads[8].end.x - xmon_center1.x  -  shift_md_x_side) / 16) ** 2) ** 0.5,
                            5 * (contact_pads[8].end.x - xmon_center1.x  -  shift_md_x_side) / 16 - 140e3],
            turn_angles=[atan2(contact_pads[8].end.y - xmon_center1.y,
                                9 * (contact_pads[8].end.x - xmon_center1.x  -  shift_md_x_side) / 16), 
                         -atan2(contact_pads[8].end.y - xmon_center1.y,
                                9 * (contact_pads[8].end.x - xmon_center1.x -  shift_md_x_side) / 16)],
            trans_in=Trans.R180
        )
        self.cpwrl_md5.place(tmp_reg)

        self.cpwrl_md5_end = MDriveLineEnd(list(self.cpwrl_md5.primitives.values())[-1], md_z1_params, md_transition, md_z1_length)
        self.cpwrl_md5_end.place(tmp_reg)      
      

        # place caplanar line 4 fl
        

        self.cpwrl_fl5 = CPW_RL_Path(
            contact_pads[7].end, shape="LRL", cpw_parameters=z_md_fl,
            turn_radiuses=[ctr_line_turn_radius],
            segment_lengths=[(contact_pads[7].end.x - xmon_center1.x ), (
                    -contact_pads[7].end.y + xmon_center1.y - shift_fl_y)],
            turn_angles=[-pi / 2], trans_in=Trans.R180
        )
        self.cpwrl_fl5.place(tmp_reg)        

        self.cpwrl_fl5_end = FluxLineEnd(self.cpwrl_fl5.end, z_md_fl, width=flux_end_width, trans_in=Trans.R0)
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


        for xmon_cross in self.xmons1:
            squid_center = (xmon_cross.cpw_bempt.start + xmon_cross.cpw_bempt.end) / 2
            squid = AsymSquid(squid_center, new_pars_squid, 0)
            squid.place(self.region_el)
            

if __name__ == "__main__":
    design = Design5Q("testCell")
    design.draw()
    design.lv.zoom_fit()
