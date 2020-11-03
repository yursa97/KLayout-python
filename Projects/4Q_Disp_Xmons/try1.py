from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload
import classLib
reload(classLib)

from classLib.coplanars import CPW, CPWParameters, CPW_RL_Path
from classLib.shapes import XmonCross
from classLib.contactPads import ContactPad

from classLib.coplanars import CPW, CPW_arc, Coil_type_1, CPW_RL_Path
from classLib.shapes import XmonCross
from classLib.baseClasses import ComplexBase
from classLib.chipTemplates import CHIP_10x10_12pads

from classLib.resonators import EMResonator_TL2Qbit_worm3_2_XmonFork


class EMResonatorTL2QbitWormRLTail(ComplexBase):
    """
    same as `EMResonator_TL2Qbit_worm3` but shorted and open ends are
    interchanged their places. In addition, a few primitives had been renamed.
    """

    def __init__(self, Z0, start, L_coupling, L0, L1, r, N,
                 tail_shape, tail_turn_radiuses,
                 tail_segment_lengths, tail_turn_angles,
                 tail_trans_in=None, trans_in=None):
        """

        Parameters
        ----------
        Z0
        start
        L_coupling
        L0
        L1
        r
        L2
        N
        L3
        tail_direction : str
            "left" - end of the resonator will be located to
            the left from long vertical line.
            "right" - end of the resonator will be located to
            the right from long vertical line.
            Try to change this parameter to get the difference.
        trans_in
        """
        self.Z0 = Z0
        self.L_coupling = L_coupling
        self.L0 = L0
        self.L1 = L1
        self.r = r
        self.N = N
        self.tail_shape = tail_shape
        self.tail_turn_radiuses = tail_turn_radiuses
        self.tail_segment_lengths = tail_segment_lengths
        self.tail_turn_angles = tail_turn_angles
        self.tail_trans_in = tail_trans_in

        super().__init__(start, trans_in)

        self._geometry_parameters["cpw_width, um"] = Z0.width / 1e3
        self._geometry_parameters["cpw_gap, um"] = Z0.gap / 1e3
        self._geometry_parameters["L_coupling, um"] = L_coupling / 1e3
        self._geometry_parameters["L0, um"] = L0 / 1e3
        self._geometry_parameters["L1, um"] = L1 / 1e3
        self._geometry_parameters["r, um"] = r / 1e3
        self._geometry_parameters["L2, um"] = L2 / 1e3
        self._geometry_parameters["L3, um"] = L2 / 1e3
        self._geometry_parameters["N"] = N

        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

    def init_primitives(self):
        self.arc1 = CPW_arc(self.Z0, DPoint(0, 0), -self.r, pi / 2)
        self.primitives["arc1"] = self.arc1

        p1 = self.arc1.end
        p2 = self.arc1.end + DPoint(0, -self.L0)
        self.cop_vertical = CPW(start=p1, end=p2, cpw_params=self.Z0)
        # open end tail face is separated from ground by `b = width + 2*gap`

        self.primitives["cop_vertical"] = self.cop_vertical

        # draw the open-circuited "tail"

        self.cpw_end_open_RLPath = CPW_RL_Path(
            self.cop_vertical.end, self.tail_shape, cpw_parameters=self.Z0,
            turn_radiuses=self.tail_turn_radiuses,
            segment_lengths=self.tail_segment_lengths,
            turn_angles=self.tail_turn_angles,
            trans_in=self.tail_trans_in
        )
        self.primitives["cpw_end_open_RLPath"] = self.cpw_end_open_RLPath

        self.cpw_end_open_gap = CPW(
            0, self.Z0.b / 2,
            self.cpw_end_open_RLPath.end,
               self.cpw_end_open_RLPath.end - DPoint(0, self.Z0.b)
        )
        self.primitives["cpw_end_open_gap"] = self.cpw_end_open_gap

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

        self.connections = [DPoint(0, 0), self.cpw_end_open_RLPath.end]
        self.angle_connections = [0, self.cpw_end_open_RLPath.alpha_end]


class EMResonatorTL2QbitWormRLTailXmonFork(EMResonatorTL2QbitWormRLTail):
    def __init__(
            self, Z0, start, L_coupling, L0, L1, r, N,
            tail_shape, tail_turn_radiuses,
            tail_segment_lengths, tail_turn_angles,
            fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap,
            tail_trans_in=None, trans_in=None
    ):
        self.fork_x_span = fork_x_span
        self.fork_y_span = fork_y_span
        self.fork_metal_width = fork_metal_width
        self.fork_gnd_gap = fork_gnd_gap

        super().__init__(
            Z0, start, L_coupling, L0, L1, r, N,
            tail_shape, tail_turn_radiuses,
            tail_segment_lengths, tail_turn_angles,
            tail_trans_in=tail_trans_in,
            trans_in=trans_in
        )

        self._geometry_parameters["fork_x_span, um"] = fork_x_span / 1e3
        self._geometry_parameters["fork_y_span, um"] = fork_y_span / 1e3
        self._geometry_parameters["fork_metal_width, um"] = fork_metal_width / 1e3
        self._geometry_parameters["fork_gnd_gap, um"] = fork_gnd_gap / 1e3

    def init_primitives(self):
        super().init_primitives()

        """ add fork to the end of the resonator """
        # adding fork horizontal part
        self.draw_fork_along_x()
        self.draw_fork_along_y()

        # remove open end from the resonator
        del self.primitives["cpw_end_open_gap"]
        del self.cpw_end_open_gap

    def draw_fork_along_x(self):
        forkZ = CPW(self.fork_metal_width, self.fork_gnd_gap)
        p1 = self.cpw_end_open_gap.start + DPoint(-self.fork_x_span / 2, -forkZ.b / 2)
        p2 = p1 + DPoint(self.fork_x_span, 0)
        self.fork_x_cpw = CPW(forkZ.width, forkZ.gap, p1, p2)
        self.primitives["fork_x_cpw"] = self.fork_x_cpw

        # draw waveguide that was erased during `fork_x_cpw` ground erasing
        p1 = self.cpw_end_open_gap.start
        p2 = self.cpw_end_open_gap.start + DPoint(0, -forkZ.gap)
        erased_cpw = CPW(self.Z0.width, self.Z0.gap, p1, p2)
        self.primitives["erased_cpw"] = erased_cpw

        # erase additional spaces at the ends of fork_x_cpw
        p1 = self.fork_x_cpw.start
        p2 = self.fork_x_cpw.start + DPoint(-forkZ.gap, 0)
        self.primitives["erased_fork_left"] = CPW(0, forkZ.b / 2, p1, p2)

        p1 = self.fork_x_cpw.end
        p2 = self.fork_x_cpw.end + DPoint(forkZ.gap, 0)
        self.primitives["erased_fork_right"] = CPW(0, forkZ.b / 2, p1, p2)

    def draw_fork_along_y(self):
        forkZ = CPW(self.fork_metal_width, self.fork_gnd_gap)

        # draw left part
        p1 = self.fork_x_cpw.start + DPoint(forkZ.width / 2, -forkZ.width / 2)
        p2 = p1 + DPoint(0, -self.fork_y_span)
        self.fork_y_cpw1 = CPW(forkZ.width, forkZ.gap, p1, p2)
        self.primitives["fork_y_cpw1"] = self.fork_y_cpw1

        # draw right part
        p1 = self.fork_x_cpw.end + DPoint(-forkZ.width / 2, -forkZ.width / 2)
        p2 = p1 + DPoint(0, -self.fork_y_span)
        self.fork_y_cpw2 = CPW(forkZ.width, forkZ.gap, p1, p2)
        self.primitives["fork_y_cpw2"] = self.fork_y_cpw2

        # erase gap at the ends of `y` fork parts
        p1 = self.fork_y_cpw1.end
        p2 = self.fork_y_cpw1.end + DPoint(0, -forkZ.gap)
        self.primitives["erased_fork_left_cpw_end"] = CPW(0, forkZ.b / 2, p1, p2)
        p1 = self.fork_y_cpw2.end
        p2 = self.fork_y_cpw2.end + DPoint(0, -forkZ.gap)
        self.primitives["erased_fork_right_cpw_end"] = CPW(0, forkZ.b / 2, p1, p2)


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

    class CPWResonator2(ComplexBase):
    # neck doesn't stand out and instead spreads along the resonator
     c = 299792458.0

    def __init__(self, origin, cpw_parameters, turn_radius, frequency, ɛ,
        wavelength_fraction = 1/4, coupling_length = 200e3,
        meander_periods = 4, neck_length = 100e3, no_neck=False, extra_neck_length=0, end_primitive=None, trans_in = None):
        """
        A CPW resonator of wavelength fraction with automatic length calculation
        from given frequency.

        Modification: with a neck along the resonator

        It is also possible to attach a primitive to the end of the resonator which
        should provide a get_phase_shift(   ) method to calculate its effective length
        as if it was just a straight CPW piece.

        Parameters:
            origin: DPoint
                The point where the resonator's coupling tail starts
            cpw_parameters: CPWParameters
                CPW parameters for the resonator
            turn_radius: float
                Raduis of the resonator's meander turns
            frequency: float, GHz
                The frequency that the resonator will have
            ɛ: float
                Substrate relative permittivity
            wavelength_fraction: float
                The fraction of the wavelength the resonator's
                fundamental mode has at resonance. This parameter
                is not checked for consistency with the resonator's
                boundaries
            coupling_length: float
                The length of the segment parallel to the feedline
            meander_periods: int
                The number of periods in the meandering part
            neck_length: float
                The length of the straight part before the uncoupled end
                of the resonator
            no_neck: bool
                If no_neck is true then the neck is absent
            extra_neck_length: float
                The length of the segment perpendicular to the neck
        """
        self.Z = cpw_parameters
        self.R = turn_radius
        self.cpl_L = coupling_length
        self.N = meander_periods
        self.neck = neck_length
        self.freq = frequency
        self.wavelength_fraction = wavelength_fraction
        self.eps = ɛ
        self.no_neck = no_neck
        self.extra_neck_length = extra_neck_length
        self.len = self._calculate_total_length()

        self.line = None # RL path that represents meandr
        self.open_end = end_primitive # open-ended coplanar at the and of the resonator

        super().__init__(origin, trans_in)

        self.start = self.line.connections[0]
        self.end = self.line.connections[1]
        self.alpha_start = self.line.angle_connections[0]
        self.alpha_end = self.line.angle_connections[1]

    def init_primitives(self):
        origin = DPoint(0, 0)
        total_neck_length =  pi * self.R / 2 + self.neck if not self.no_neck else 0
        meander_length = (self.len - self.cpl_L - 2 * (1 + self.N) * pi * self.R - 3 * self.R - total_neck_length - self.extra_neck_length) / (2 * self.N + 3 / 2)
        shape = "LRL" + self.N * "RLRL" + "RL" + ("RL" if not self.no_neck else "")
        segment_lengths = [self.cpl_L, meander_length] + 2 * self.N * [meander_length] + [meander_length + 3 * self.R + self.extra_neck_length] + ([self.neck] if not self.no_neck else [])
        turn_angles = [pi] + self.N * [-pi, pi]+[-pi] + ([-pi/2] if not self.no_neck else [])

        self.line = CPW_RL_Path(origin, shape, self.Z, self.R, segment_lengths, turn_angles)
        self.primitives['line'] = self.line

        if self.open_end == None:
            self.open_end = CPW(0, self.Z.b/2, self.line.end, self.line.end + (DPoint(0, -self.Z.b) if not self.no_neck else DPoint(-self.Z.b, 0)))
        self.primitives['open_end'] = self.open_end

    def _calculate_total_length(self):
        length = self._c / self.freq / sqrt(self.eps/2 + 0.5) / 1e9 * self.wavelength_fraction
        return length * 1e9 # in nm

class EMResonator_TL2Qbit_worm(ComplexBase):
    def __init__( self, Z0, start, L_coupling, L1, r, L2, N, trans_in=None ):
        self.Z0 = Z0
        self.L_coupling = L_coupling
        self.L1 = L1
        self.r = r
        self.L2 = L2

        self.N = N
        self.primitives_gnd = {}
        super().__init__( start, trans_in )

        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

    def init_primitives( self ):
        name = "coil0"
        setattr(self, name, Coil_type_1(self.Z0, DPoint(0,0), self.L_coupling, self.r, self.L1) )
        self.primitives[name] = getattr( self, name )
        # coils filling
        for i in range(self.N):
            name = "coil" + str(i+1)
            setattr( self, name, Coil_type_1( self.Z0, DPoint( -self.L1 + self.L_coupling, -(i+1)*(4*self.r) ), self.L1, self.r, self.L1 ) )
            self.primitives[name] = getattr( self, name )

        # draw the "tail"
        self.arc_tail = CPW_arc( self.Z0, self.primitives["coil" + str(self.N)].end, -self.L1/2, -pi/2 )
        self.cop_tail = CPW( self.Z0.width, self.Z0.gap, self.arc_tail.end, self.arc_tail.end - DPoint( 0,self.L2 ) )
        self.cop_open_end = CPW( 0, self.Z0.b/2, self.cop_tail.end, self.cop_tail.end - DPoint(0,self.Z0.b) )
        self.primitives["arc_tail"] = self.arc_tail
        self.primitives["cop_tail"] = self.cop_tail
        self.primitives["cop_open_end"] = self.cop_open_end

        self.connections = [DPoint(0,0), self.cop_tail.end]
        self.angle_connections = [0,self.cop_tail.alpha_end]
    ## DRAWING SECTION START ##
    origin = DPoint(0, 0)
    
    # main drive line coplanar
    x = None
    y = 0.9 * CHIP_10x10_12pads.dy
    p1 = DPoint(0, y)
    p2 = DPoint(CHIP_10x10_12pads.dx, y)
    Z0 = CPW(CHIP_10x10_12pads.cpw_width, CHIP_10x10_12pads.cpw_gap, p1, p2)
    
    # resonator
    # corresponding to resonanse freq is somewhere near 5 GHz
    L_coupling_list = [250e3]*2
    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L0 = 1600e3
    L1_list = [1e3 * x for x in [86.3011, 79.9939]]
    estimated_res_freqs_init = [4.932, 5.0]  # GHz
    freqs_span_corase = 1.0  # GHz
    freqs_span_fine = 0.005
    r = 50e3
    N = 7
    L2_list = [0.0e3] * len(L1_list)
    L3 = 0
    width_res = 20e3
    gap_res = 10e3
    Z_res = CPW(width_res, gap_res, origin, origin)
    to_line = 53e3

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
    xmon_fork_penetrations = [-20e3, -10e3]

    # clear this cell and layer
    cell.clear()
    tmp_reg = Region()  # faster to call `place` on single region

    # place chip metal layer
    chip_box = pya.Box(DPoint(0, 0), DPoint(CHIP_10x10_12pads.dx, CHIP_10x10_12pads.dy))
    tmp_reg.insert(chip_box)
    contact_pads = CHIP_10x10_12pads.get_contact_pads()
    for contact_pad in contact_pads:
        contact_pad.place(tmp_reg)

    # place readout waveguide
    ro_line_turn_radius = 200e3
    ro_line_dy = 600e3
    cpwrl_ro = CPW_RL_Path(
        contact_pads[-1].end, shape="LRLRL", cpw_parameters=Z0,
        turn_radiuses=[ro_line_turn_radius]*2,
        segment_lengths=[ro_line_dy, CHIP_10x10_12pads.pcb_feedline_d, ro_line_dy],
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
            worm_x = 1.2 * CHIP_10x10_12pads.pcb_feedline_d
        else:
            worm_x = 1.2 * CHIP_10x10_12pads.pcb_feedline_d + res_idx * xmon_x_distance - \
                     (L_coupling_list[res_idx] - L_coupling_list[0]) + \
                     (L1_list[res_idx] - L1_list[0]) / 2
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

