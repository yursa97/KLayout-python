# Enter your Python code here
import pya
from math import cos, sin, atan2, pi
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans
from classLib.coplanars import CPW, CPW_arc
from classLib.resonators import Coil_type_1
from classLib.baseClasses import ComplexBase, ElementBase

from importlib import reload
import sonnetSim.sonnetLab

reload(sonnetSim.sonnetLab)
from sonnetSim.sonnetLab import SonnetLab, SonnetPort, SimulationBox
from classLib.shapes import XmonCross


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


class CHIP:
    dx = 0.2e6
    dy = 0.2e6
    L1 = 2.5e6
    gap = 150.e3
    width = 260.e3
    b = 2 * gap + width
    origin = DPoint(0, 0)
    center = DPoint(dx / 2, dy / 2)
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
    origin = DPoint(0, 0)

    import itertools
    cross_len_x_list = [1e3 * x for x in range(140, 201, 20)]
    cross_width_list = itertools.repeat(60e3)
    cross_len_y_list = itertools.repeat(125e3)
    cross_gnd_gap_x_list = itertools.repeat(20e3)
    cross_gnd_gap_y_list = itertools.repeat(30e3)

    # clear this cell and layer
    cell.clear()

    from itertools import product

    pars = zip(cross_len_x_list, cross_width_list, cross_len_y_list, cross_gnd_gap_x_list, cross_gnd_gap_y_list)
    for par in pars:
        # unpacking parameters
        cross_len_x = par[0]
        cross_width_x = par[1]
        cross_len_y = par[2]
        cross_gnd_gap_x = par[3]
        cross_gnd_gap_y = par[4]

        xmon_dX = 2 * cross_len_x + cross_width_x + 2 * cross_gnd_gap_x
        CHIP.dx = 5 * xmon_dX
        CHIP.dy = 5 * xmon_dX
        CHIP.center = DPoint(CHIP.dx / 2, CHIP.dy / 2)

        chip_box = pya.Box(Point(0, 0), Point(CHIP.dx, CHIP.dy))
        cell.shapes(layer_photo).insert(chip_box)

        xmon_cross1 = XmonCross(
            CHIP.center,
            cross_len_x, cross_width_x, cross_gnd_gap_x,
            sideY_length=cross_len_y, sideY_gnd_gap=cross_gnd_gap_y
        )
        xmon_cross1.place(cell, layer_photo)

        ## DRAWING SECTION END ##
        # lv.zoom_fit()

        ### MATLAB COMMANDER SECTION START ###
        ml_terminal = SonnetLab()
        print("starting connection...")
        from sonnetSim.cMD import CMD

        ml_terminal._send(CMD.SAY_HELLO)
        ml_terminal.clear()
        simBox = SimulationBox(CHIP.dx, CHIP.dy, 600, 600)
        ml_terminal.set_boxProps(simBox)
        print("sending cell and layer")
        from sonnetSim.pORT_TYPES import PORT_TYPES

        ports = [
            SonnetPort(xmon_cross1.cpw_l.end, PORT_TYPES.AUTOGROUNDED)
        ]
        ml_terminal.set_ports(ports)

        ml_terminal.send_polygons(cell, layer_photo)
        ml_terminal.set_linspace_sweep(0.01, 0.01, 1)
        print("simulating...")
        result_path = ml_terminal.start_simulation(wait=True)
        # print("visualizing...")
        # ml_terminal.visualize_sever()
        ml_terminal.release()

        # get the .csv result file and exctract capcity of island in fF
        import shutil
        import os
        import csv

        project_dir = os.path.dirname(__file__)

        C1 = None
        with open(result_path.decode("ascii"), "r", newline='') as csv_file:
            data_rows = list(csv.reader(csv_file))
            ports_imps_row = data_rows[6]
            R = float(ports_imps_row[0].split(' ')[1])
            data_row = data_rows[8]
            freq0 = float(data_row[0])
            re_s11 = float(data_row[1])
            im_s11 = float(data_row[2])
            import math

            s11 = complex(re_s11, im_s11)
            y11 = 1 / R * (1 - s11) / (1 + s11)
            C1 = -1e15 / (2 * math.pi * freq0 * 1e9 * (1 / y11).imag)

        print(C1)

        output_filepath = os.path.join(project_dir, "Xmon_C1.csv")
        if os.path.exists(output_filepath):
            # append data to file
            with open(output_filepath, "a", newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow([cross_width_x / 1e3, cross_len_x / 1e3, cross_gnd_gap_x / 1e3, cross_len_y, C1])
        else:
            # create file, add header, append data
            with open(output_filepath, "w", newline='') as csv_file:
                writer = csv.writer(csv_file)
                # create header of the file
                writer.writerow(["cross_width, um", "cross_len, um", "cross_gnd_gap, um", "cross_len_y, um", "C12, fF"])
                writer.writerow([cross_width_x / 1e3, cross_len_x / 1e3, cross_gnd_gap_x / 1e3, cross_len_y/1e3, C1])


