# Enter your Python code here
import pya
from math import cos, sin, atan2, pi
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from сlassLib.baseClasses import ComplexBase
from сlassLib.coplanars import CPW, CPW_arc
from сlassLib.resonators import Coil_type_1
from сlassLib.shapes import XmonCross

from sonnetSim.sonnetLab import SonnetLab, SonnetPort, SimulationBox


class EMResonator_TL2Qbit_worm2(ComplexBase):
    def __init__(self, Z0, start, L_coupling, L1, r, L2, N, trans_in=None):
        self.Z0 = Z0  # resonator's coplanar waveguide parameters
        # first horizontal coplanar length.
        # Usually located near readout waveguide, hence the name origin
        self.L_coupling = L_coupling
        self.L1 = L1  # horizontal coplanars length
        self.r = r  # curvature radius of all arc coplanars
        self.L2 = L2  # tail length

        self.N = N  # number of Coil_type_1 structure utilized
        super().__init__(start, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

    def init_primitives(self):
        self.arc1 = CPW_arc(self.Z0, DPoint(0, 0), -self.r, pi / 2)
        self.primitives["arc1"] = self.arc1

        # making coil
        name = "coil0"
        setattr(self, name, Coil_type_1(self.Z0, DPoint(0, 0), self.L_coupling, self.r, self.L1))
        self.primitives[name] = getattr(self, name)
        # coils filling
        for i in range(self.N):
            name = "coil" + str(i + 1)
            prev_coil_end = getattr(self, "coil" + str(i)).connections[-1]
            setattr(
                self, name,
                Coil_type_1( self.Z0, prev_coil_end, self.L1, self.r, self.L1)
            )
            self.primitives[name] = getattr(self, name)

        # draw the "tail"
        self.arc_tail = CPW_arc(self.Z0, self.primitives["coil" + str(self.N)].end, -self.L1 / 2, -pi / 2)
        self.cop_tail = CPW(self.Z0.width, self.Z0.gap, self.arc_tail.end, self.arc_tail.end - DPoint(0, self.L2))

        # tail face is separated from ground by `b = width + 2*gap`
        self.cop_open_end = CPW(0, self.Z0.b / 2, self.cop_tail.end, self.cop_tail.end - DPoint(0, self.Z0.b))
        self.primitives["arc_tail"] = self.arc_tail
        self.primitives["cop_tail"] = self.cop_tail
        self.primitives["cop_open_end"] = self.cop_open_end

        self.connections = [DPoint(0, 0), self.cop_tail.end]
        self.angle_connections = [0, self.cop_tail.alpha_end]


class EMResonator_TL2Qbit_worm2_XmonFork(EMResonator_TL2Qbit_worm2):
    def __init__(self, Z0, start, L_coupling, L1, r, L2, N,
                 fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap,
                 trans_in=None):
        self.fork_x_span = fork_x_span
        self.fork_y_span = fork_y_span
        self.fork_metal_width = fork_metal_width
        self.fork_gnd_gap = fork_gnd_gap

        super().__init__(Z0, start, L_coupling, L1, r, L2, N, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

    def init_primitives(self):
        super().init_primitives()

        """ add fork to the end of the resonator """
        # remove open end from the resonator
        del self.primitives["cop_open_end"]
        del self.cop_open_end

        # adding fork
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


class CHIP:
    dx = 0.6e6
    dy = 1.8e6
    L1 = 2.5e6
    gap = 150.e3
    width = 260.e3
    b = 2 * gap + width
    origin = DPoint(0, 0)
    center = DPoint(dx/2, dy/2)
    box = pya.DBox(origin, origin + DPoint(dx, dy))
    # only 4 connections programmed by now
    connections = [box.p1 + DPoint(L1 + b / 2, 0), box.p1 + DPoint(dx - (L1 + b / 2), 0),
                   box.p2 - DPoint(L1 + b / 2, 0), box.p1 + DPoint(L1 + b / 2, dy)]


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
    chip_box = pya.Box(Point(0, 0), Point(CHIP.dx, CHIP.dy))
    origin = DPoint(0, 0)

    contact_L = 1e6

    # main drive line coplanar
    width = 24.1e3
    gap = 12.95e3
    x = 0.25 * CHIP.dx
    y = 0.9 * CHIP.dy
    p1 = DPoint(0, y)
    p2 = DPoint(CHIP.dx, y)
    Z0 = CPW(width, gap, p1, p2)

    # resonator
    L_coupling = 300e3
    # corresponding to resonanse freq is linspaced in interval [6,9) GHz
    L1 = 100e3
    r = 100e3
    L2 = 270e3
    gnd_width = 35e3
    N = 4
    width_res = 9.6e3
    gap_res = 5.2e3
    to_line = 35e3
    Z_res = CPW(width_res, gap_res)

    # xmon cross parameters
    cross_width = 60e3
    cross_len = 125e3
    cross_gnd_gap = 20e3

    # fork at the end of resonator parameters
    fork_metal_width = 20e3
    fork_gnd_gap = 20e3
    xmon_fork_gnd_gap = 20e3
    fork_x_span = cross_width + 2*(xmon_fork_gnd_gap + fork_metal_width)
    fork_y_span = None
    # Xmon-fork parameters
    xmon_fork_penetrations = [1e3*x for x in [-10, -20]]
    for xmon_fork_penetration in xmon_fork_penetrations:
        # clear this cell and layer
        cell.clear()
        fork_y_span = xmon_fork_penetration + xmon_fork_gnd_gap
        worm = EMResonator_TL2Qbit_worm2_XmonFork(
            Z_res, origin, L_coupling, L1, r, L2, N,
            fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap
        )
        xmon_center = (worm.fork_y_cpw1.end + worm.fork_y_cpw2.end)/2
        xmon_center += DPoint(0, -(cross_len + cross_width / 2) + xmon_fork_penetration)
        xmonCross = XmonCross(xmon_center, cross_width, cross_len, cross_gnd_gap)
        # cutting everything out except for the tail that will be capcitavely coupled
        # to Xmon
        for key in list(worm.primitives.keys()):
            if (key == "cop_tail") or key.startswith("fork") or key.startswith("erased"):
                pass
            else:
                del worm.primitives[key]

        # calculate bounding box dimensions
        tmp_reg = Region()
        worm.place(tmp_reg)
        xmonCross.place(tmp_reg)
        bbox = tmp_reg.bbox()

        # calculate simulation box dimensions
        CHIP.dx = 3*bbox.width()
        CHIP.dy = 2*bbox.height()
        chip_p1 = DPoint(bbox.center()) + DPoint(-0.5*CHIP.dx, -0.5*CHIP.dy)
        chip_p2 = DPoint(bbox.center()) + DPoint(0.5*CHIP.dx, 0.5*CHIP.dy)
        chip_box = pya.Box(DPoint(0, 0), DPoint(CHIP.dx, CHIP.dy))

        # forming resonator's tail upper side open-circuited for simulation
        p1 = worm.cop_tail.start
        p2 = p1 + DPoint(0, 20e3)
        empty_cpw_tail_start = CPW(0, Z_res.b/2, p1, p2)

        # placing all objects in proper order and translating them to origin
        cell.shapes(layer_photo).insert(chip_box)

        # translating all objects so that chip.p1 at coordinate origin
        translation_trans = DCplxTrans(-DVector(chip_p1))

        xmonCross.make_trans(translation_trans)
        xmonCross.place(cell, layer_photo)

        worm.make_trans(translation_trans)
        worm.place(cell, layer_photo)

        empty_cpw_tail_start.place(cell, layer_photo)
        empty_cpw_tail_start.make_trans(translation_trans)
        empty_cpw_tail_start.place(cell, layer_photo)

        xmonCross_corrected = XmonCross(xmon_center, cross_width, cross_len, xmon_fork_gnd_gap)
        xmonCross_corrected.make_trans(translation_trans)
        xmonCross_corrected.place(cell, layer_photo)

        ## DRAWING SECTION END ##
        lv.zoom_fit()

        ### MATLAB COMMANDER SECTION START ###
        ml_terminal = SonnetLab()
        print("starting connection...")
        from sonnetSim.cMD import CMD

        ml_terminal._send(CMD.SAY_HELLO)
        ml_terminal.clear()
        simBox = SimulationBox(CHIP.dx, CHIP.dy, 900, 1200)
        ml_terminal.set_boxProps(simBox)
        print("sending cell and layer")
        from sonnetSim.pORT_TYPES import PORT_TYPES

        ports = [
            SonnetPort(worm.cop_tail.start, PORT_TYPES.AUTOGROUNDED),
            SonnetPort(xmonCross.cpw_b.end, PORT_TYPES.AUTOGROUNDED)
        ]
        ml_terminal.set_ports(ports)

        ml_terminal.send_polygons(cell, layer_photo)
        ml_terminal.set_linspace_sweep(0.01, 0.01, 1)
        print("simulating...")
        result_path = ml_terminal.start_simulation(wait=True)
        ml_terminal.release()

        # get the .csv result file and exctract capcity of island in fF
        import os
        import csv
        project_dir = os.path.dirname(__file__)

        C_qr = None
        C1 = None

        with open(result_path.decode("ascii"), "r") as csv_file:
            data_rows = list(csv.reader(csv_file))
            ports_imps_row = data_rows[6]
            R = float(ports_imps_row[0].split(' ')[1])
            data_row = data_rows[8]
            freq0 = float(data_row[0])

            s = [[0, 0], [0, 0]]  # s-matrix
            for i in range(0, 2):
                for j in range(0, 2):
                    s[i][j] = complex(float(data_row[1 + 2 * (i * 2 + j)]), float(data_row[1 + 2 * (i * 2 + j) + 1]))
            import math

            # formula to transform S-params to Y-params is taken from
            # https://en.wikipedia.org/wiki/Admittance_parameters#Two_port

            # calculations for C1 and C12 are taken from Sonnet equation plotting
            delta = (1 + s[0][0]) * (1 + s[1][1]) - s[0][1] * s[1][0]
            y21 = -2 * s[1][0] / delta * 1 / R
            C_qr = 1e15 / (2 * math.pi * freq0 * 1e9 * (1 / y21).imag)

            y11 = ((1 - s[0][0])*(1 + s[1][1]) + s[0][1]*s[1][0]) / delta * 1/R
            C1 = -1e15 / (2 * math.pi * freq0 * 1e9 * (1 / y11).imag)

        print(C_qr, "  ", C1)

        output_filepath = os.path.join(project_dir, "Xmon_resonator_Cg.csv")
        if os.path.exists(output_filepath):
            # append data to file
            with open(output_filepath, "a") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(
                    [cross_width / 1e3, cross_len / 1e3, cross_gnd_gap / 1e3,
                     xmon_fork_penetration / 1e3, xmon_fork_gnd_gap / 1e3, C1, C_qr / C1]
                )
        else:
            # create file, add header, append data
            with open(output_filepath, "w") as csv_file:
                writer = csv.writer(csv_file)
                # create header of the file
                writer.writerow(
                    ["cross_width, um", "cross_len, um", "cross_gnd_gap, um",
                     "xmon_fork_penetration, um", "xmon_fork_gnd_gap, um", "C1, fF", "beta"])
                writer.writerow(
                    [cross_width / 1e3, cross_len / 1e3, cross_gnd_gap / 1e3,
                     xmon_fork_penetration / 1e3, xmon_fork_gnd_gap/1e3, C1, C_qr / C1]
                )