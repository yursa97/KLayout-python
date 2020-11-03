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

#from classLib.resonators import EMResonator_TL2Qbit_worm4_XmonFork

# NOT TESTED, ERRORS CAN BE FIGURED OUT EASILY

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
#        self.arc1 = CPW_arc(self.Z0, DPoint(0, 0), -self.r, pi / 2)
#        self.primitives["arc1"] = self.arc1

#        p1 = self.arc1.end
#        p2 = self.arc1.end + DPoint(0, -self.L0)
#        self.L0_cpw = CPW(start=p1, end=p2, cpw_params=self.Z0)
#        self.primitives["L0_cpw"] = self.L0_cpw

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
                 fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap,
                 trans_in=None):
        self.fork_x_span = fork_x_span
        self.fork_y_span = fork_y_span
        self.fork_metal_width = fork_metal_width
        self.fork_gnd_gap = fork_gnd_gap

        super().__init__(
            Z0, start, L_coupling, L0, L1, r, L2, N, trans_in
        )

        self._geometry_parameters["fork_x_span, um"] = fork_x_span / 1e3
        self._geometry_parameters["fork_y_span, um"] = fork_y_span / 1e3
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
        self.draw_fork_along_y()

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
        p1 = self.fork_y_cpw1.end + DPoint(0, -forkZ.gap)
        self.primitives["erased_fork_left_cpw_end"] = CPW(0, forkZ.b / 2, self.fork_y_cpw1.end, p1)
        p1 = self.fork_y_cpw2.end + DPoint(0, -forkZ.gap)
        self.primitives["erased_fork_right_cpw_end"] = CPW(0, forkZ.b / 2, self.fork_y_cpw2.end, p1)

# horisntal part 2

        self.draw_fork_along_x_new()
        self.draw_fork_along_y_new()

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

    def draw_fork_along_y_new(self):
        forkZ_new = CPW(self.fork_metal_width, self.fork_gnd_gap)

        # draw left part
        p1 = self.fork_x_cpw_new.start + DPoint(forkZ_new.width / 2, -forkZ_new.width / 2)
        p2 = p1 + DPoint(0, -self.fork_y_span)
        self.fork_y_cpw1_new = CPW(forkZ_new.width, forkZ_new.gap, p1, p2)
        self.primitives["fork_y_cpw1_new"] = self.fork_y_cpw1_new

        # draw right part
        p1 = self.fork_x_cpw_new.end + DPoint(-forkZ_new.width / 2, -forkZ_new.width / 2)
        p2 = p1 + DPoint(0, -self.fork_y_span)
        self.fork_y_cpw2_new = CPW(forkZ_new.width, forkZ_new.gap, p1, p2)
        self.primitives["fork_y_cpw2_new"] = self.fork_y_cpw2_new

        # erase gap at the ends of `y` fork parts
        p1 = self.fork_y_cpw1_new.end + DPoint(0, -forkZ_new.gap)
        self.primitives["erased_fork_left_cpw_end_new"] = CPW(0, forkZ_new.b / 2, self.fork_y_cpw1_new.end, p1)
        p1 = self.fork_y_cpw2_new.end + DPoint(0, -forkZ_new.gap)
        self.primitives["erased_fork_right_cpw_end_new"] = CPW(0, forkZ_new.b / 2, self.fork_y_cpw2_new.end, p1)


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
#    box = pya.DBox(origin, origin + DPoint(dx, dy))
    L1 = 0
    # only 4 connections programmed by now
#    connections = [box.p1 + DPoint(L1 + b / 2, 0), box.p1 + DPoint(dx - (L1 + b / 2), 0),
 #                  box.p2 - DPoint(L1 + b / 2, 0), box.p1 + DPoint(L1 + b / 2, dy)]

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

    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L0 = 0 #1700e3
    L1_list = [1e3 * x for x in [79.3927]]
    estimated_res_freqs = [5.0209]  # GHz
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
    stab_gnd_gap = 2.5e3
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

    L_coupling = 0
    to_line_list = [1e3*x for x in [120]]
    pars = map(
        lambda x: list(x[0]) + [x[1]],
        itertools.product(zip(L1_list, L2_list, estimated_res_freqs), to_line_list)
    )

    for L1, L2, estimated_freq, to_line in pars:
        # clear this cell and layer
        cell.clear()
        fork_y_span = xmon_fork_penetration + xmon_fork_gnd_gap
        worm_x = CHIP.dx / 2
        stab_end_gnd_gap = to_line - Z_res.width/2 - Z0.b/2  # exactly to create empty coridor to the waveguide       
        worm = EMResonator_TL2Qbit_worm4_XmonFork(
            Z_res, DPoint(worm_x,0.9 * CHIP.dy - 2 * to_line), 0, 0,79.3927e3, r, 100e3, 7,
            fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap, Trans.R270
        )


        # calculate simulation box dimensions
        chip_box = pya.Box(DPoint(0, 0), DPoint(CHIP.dx, CHIP.dy))

        # placing all objects in proper order and translating them to origin
        cell.shapes(layer_photo).insert(chip_box)

        # translating all objects so that chip.p1 at coordinate origin
#        xmonCross.place(cell, layer_photo)
        worm.place(cell, layer_photo)
#        res.place(cell, layer_photo)



        Z0.place(cell, layer_photo)

        # delete Xmon cross
        shapes = cell.shapes(layer_photo)
  #      for shape in shapes.each_overlapping(pya.Box(xmon_center, xmon_center)):
            # if shape is polygon and contains xmon_center inside
            # then delete this polygon
 #           if shape.is_polygon and shape.polygon.inside(xmon_center):
     #           shape.delete()

        ## DRAWING SECTION END ##
        lv.zoom_fit()
