# Enter your Python code here
from math import cos, sin, atan2, pi
import itertools

import pya
from pya import Point, DPoint, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import Complex_Base
from ClassLib.Coplanars import CPW, CPW_arc
from ClassLib.Resonators import Coil_type_1
from ClassLib.Shapes import XmonCross

from sonnetSim.sonnetLab import SonnetLab, SonnetPort, SimulationBox
from ClassLib.Resonators import EMResonator_TL2Qbit_worm3

class EMResonator_TL2Qbit_worm4(EMResonator_TL2Qbit_worm3):
    def __init__(self, Z0, start, L_coupling, L0, L1, r, L2, N,
                 stab_width, stab_gnd_gap, stab_len, stab_end_gnd_gap, trans_in=None):
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
        Z_stab : CPWParams
        trans_in
        """
        self.stab_width = stab_width
        self.stab_gnd_gap = stab_gnd_gap
        self.stab_len = stab_len
        self.stab_end_gnd_gap = stab_end_gnd_gap

        # primitives introduced in this class
        self.Z_stab_cpw: CPW = None
        self.Z_stab_end_empty: CPW = None

        super().__init__(Z0, start, L_coupling, L0, L1, r, L2, N, trans_in)

        self._geometry_parameters.update(
            {**self.Z_stab_cpw.get_geometry_params_dict(prefix="resCoupleStab_"),
             "resCoupleStab_stab_end_gnd_gap, um": self.stab_end_gnd_gap/1e3}
        )

    def init_primitives(self):
        super().init_primitives()
        origin = DPoint(0,0)
        p1 = origin + DPoint(L_coupling/2, self.Z0.width/2)
        p2 = p1 + DPoint(0, self.stab_len)
        self.Z_stab_cpw = CPW(self.stab_width, self.stab_gnd_gap, p1, p2)
        self.primitives["Z_stab_cpw"] = self.Z_stab_cpw

        p1 = self.Z_stab_cpw.end
        p2 = p1 + DPoint(0, self.stab_end_gnd_gap)
        self.Z_stab_end_empty = CPW(0, self.Z_stab_cpw.b/2, p1, p2)
        self.primitives["Z_stab_end_empty"] = self.Z_stab_end_empty


class EMResonator_TL2Qbit_worm4_XmonFork(EMResonator_TL2Qbit_worm4):
    def __init__(self, Z0, start, L_coupling, L0, L1, r, L2, N,
                 stab_width, stab_gnd_gap, stab_len, stab_end_gnd_gap,
                 fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap,
                 trans_in=None):
        self.fork_x_span = fork_x_span
        self.fork_y_span = fork_y_span
        self.fork_metal_width = fork_metal_width
        self.fork_gnd_gap = fork_gnd_gap

        super().__init__(
            Z0, start, L_coupling, L0, L1, r, L2, N,
            stab_width, stab_gnd_gap, stab_len, stab_end_gnd_gap, trans_in
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
    freqs_span = 0.004  # GHz
    r = 50e3
    L2_list = [100e3 + 0.5 * (L1_list[0] - L1) for L1 in L1_list]
    N = 7
    width_res = 10e3
    gap_res = 10e3
    to_line = 45e3
    Z_res = CPW(width_res, gap_res, origin, origin)
    stab_width = 10e3
    stab_gnd_gap = 10e3
    stab_len = 40e3
    stab_end_gnd_gap = 10e3

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
    to_line_list = [46e3]
    pars = map(
        lambda x: list(x[0]) + [x[1]],
        itertools.product(zip(L1_list, L2_list, estimated_res_freqs), to_line_list)
    )
    for L1, L2, estimated_freq, to_line in pars:
        # clear this cell and layer
        cell.clear()
        fork_y_span = xmon_fork_penetration + xmon_fork_gnd_gap
        worm_x = CHIP.dx / 2 - L_coupling / 2
        worm = EMResonator_TL2Qbit_worm4_XmonFork(
            Z_res, DPoint(worm_x, y - to_line), L_coupling, L0, L1, r, L2, N,
            stab_width, stab_gnd_gap, stab_len, stab_end_gnd_gap,
            fork_x_span, fork_y_span, fork_metal_width, fork_gnd_gap
        )

        xmon_center = (worm.fork_y_cpw1.end + worm.fork_y_cpw2.end) / 2
        xmon_center += DPoint(0, -(cross_len + cross_width / 2) + xmon_fork_penetration)
        xmonCross = XmonCross(xmon_center, cross_width, cross_len, cross_gnd_gap)

        # calculate simulation box dimensions
        chip_box = pya.Box(DPoint(0, 0), DPoint(CHIP.dx, CHIP.dy))

        # placing all objects in proper order and translating them to origin
        cell.shapes(layer_photo).insert(chip_box)

        # translating all objects so that chip.p1 at coordinate origin
        xmonCross.place(cell, layer_photo)
        worm.place(cell, layer_photo)

        xmonCross_corrected = XmonCross(xmon_center, cross_width, cross_len, xmon_fork_gnd_gap)
        xmonCross_corrected.place(cell, layer_photo)

        Z0.place(cell, layer_photo)

        # delete Xmon cross
        shapes = cell.shapes(layer_photo)
        for shape in shapes.each_overlapping(pya.Box(xmon_center, xmon_center)):
            # if shape is polygon and contains xmon_center inside
            # then delete this polygon
            if shape.is_polygon and shape.polygon.inside(xmon_center):
                shape.delete()

        ## DRAWING SECTION END ##
        lv.zoom_fit()

        # ### MATLAB COMMANDER SECTION START ###
        # ml_terminal = SonnetLab()
        # print("starting connection...")
        # from sonnetSim.cMD import CMD
        #
        # ml_terminal._send(CMD.SAY_HELLO)
        # ml_terminal.clear()
        # simBox = SimulationBox(CHIP.dx, CHIP.dy, CHIP.nX, CHIP.nY)
        # ml_terminal.set_boxProps(simBox)
        # print("sending cell and layer")
        # from sonnetSim.pORT_TYPES import PORT_TYPES
        #
        # ports = [SonnetPort(point, PORT_TYPES.BOX_WALL) for point in [Z0.start, Z0.end]]
        # ml_terminal.set_ports(ports)
        #
        # ml_terminal.send_polygons(cell, layer_photo)
        # ml_terminal.set_ABS_sweep(estimated_freq - freqs_span / 2, estimated_freq + freqs_span / 2)
        # print("simulating...")
        # result_path = ml_terminal.start_simulation(wait=True)
        # ml_terminal.release()
        # ### MATLAB COMMANDER SECTION END ###
        #
        # ### RESULT SAVING SECTION START ###
        # import shutil
        # import os
        # import csv
        #
        # # geometry parameters gathering
        # worm_params = worm.get_geometry_params_dict(prefix="worm_")
        # xmonCross_params = xmonCross.get_geometry_params_dict(prefix="xmonCross_")
        # Z0_params = Z0.get_geometry_params_dict(prefix="S21Line_")
        # CHIP_params = CHIP.get_geometry_params_dict(prefix="chip_")
        #
        # project_dir = os.path.dirname(__file__)
        #
        # # creating directory with simulation results
        # results_dirname = "resonator_waveguide_Q_freqs_results"
        # results_dirpath = os.path.join(project_dir, results_dirname)
        #
        # output_metaFile_path = os.path.join(
        #     results_dirpath,
        #     "resonator_waveguide_Q_freq_meta.csv"
        # )
        # try:
        #     # creating directory
        #     os.mkdir(results_dirpath)
        # except FileExistsError:
        #     # directory already exists
        #     with open(output_metaFile_path, "r+", newline='') as csv_file:
        #         reader = csv.reader(csv_file)
        #         existing_entries_n = len(list(reader))
        #         Sparams_filename = "result_" + str(existing_entries_n) + ".csv"
        #
        #         writer = csv.writer(csv_file)
        #
        #         all_params_vals = list(
        #             itertools.chain(
        #                 worm_params.values(),
        #                 xmonCross_params.values(),
        #                 Z0_params.values(),
        #                 CHIP_params.values()
        #             )
        #         )
        #         # append new values row to file
        #         writer.writerow(all_params_vals + [Sparams_filename])
        # else:
        #     '''
        #         Directory has not existed and has been created sucessfully.
        #         So we create fresh meta-file.
        #         Meta-file contain simulation parameters and corresponding
        #         S-params filename that is located in this directory
        #     '''
        #     with open(output_metaFile_path, "w+", newline='') as csv_file:
        #         writer = csv.writer(csv_file)
        #         all_params_keys = list(
        #             itertools.chain(
        #                 worm_params.keys(),
        #                 xmonCross_params.keys(),
        #                 Z0_params.keys(),
        #                 CHIP_params.keys()
        #             )
        #         )
        #         all_params_vals = list(
        #             itertools.chain(
        #                 worm_params.values(),
        #                 xmonCross_params.values(),
        #                 Z0_params.values(),
        #                 CHIP_params.values()
        #             )
        #         )
        #         # create header of the file
        #         writer.writerow(all_params_keys + ["filename"])
        #         # add first parameters row
        #         reader = csv.reader(csv_file)
        #         existing_entries_n = len(list(reader))
        #         Sparams_filename = "result_1.csv"
        #         writer.writerow(all_params_vals + [Sparams_filename])
        # finally:
        #     # copy result from sonnet folder and rename it accordingly
        #     shutil.copy(
        #         result_path.decode("ascii"),
        #         os.path.join(results_dirpath, Sparams_filename)
        #     )
        # ### RESULT SAVING SECTION END ###
