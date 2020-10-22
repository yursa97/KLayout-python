from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region, Box, DBox
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload

import pickle as pkl

import ClassLib

reload(ClassLib)
from ClassLib import *

import sonnetSim

reload(sonnetSim)
from sonnetSim import SonnetLab, PORT_TYPES


class Sandbox(ChipDesign):
    def __init__(self, cell_name):
        self.origin = DPoint(0, 0)
        self.Z = CPWParameters(20e3, 10e3)  # normal CPW
        self.Z_narrow = CPWParameters(10e3, 7e3)  # narrow CPW

        self.cop_waveguide = None

        ## SIMULATION PARAMETERS SECTION START ##
        self.sim_X = 0.5e6
        self.sim_Y = 0.2e6

        self.sim_X_N = 200
        self.sim_Y_N = 200

        self.SL = None
        self.dx = 0
        self.dy = self.Z.gap/3
        self.square_height = self.Z.gap/3
        self.square_width = self.Z.gap/3
        ## SIMULATION PARAMETERS SECTION END ##

        super().__init__(cell_name)

    # Call other methods drawing parts of the design from here
    def draw(self):
        self.cell.clear()
        self.draw_sim_box()
        self.draw_waveguide()
        self.draw_square()

    def draw_sim_box(self):
        sim_box = Box(self.origin,
                      self.origin + DPoint(self.sim_X, self.sim_Y))
        self.region_ph.insert(sim_box)

    def draw_waveguide(self):
        self.cop_waveguide = CPW(cpw_params=self.Z,
                                 start=DPoint(0, self.sim_Y / 2),
                                 end=DPoint(self.sim_X, self.sim_Y / 2))
        self.cop_waveguide.place(self.region_ph)

    def draw_square(self):
        p1 = DPoint(self.sim_X / 2 + self.dx, self.sim_Y / 2 - self.Z.b/2 + self.dy)
        square = DBox(p1, p1 + DPoint(self.square_width, self.square_height))
        self.region_ph.insert(Box().from_dbox(square))

    def simulate(self):
        self.SL = SonnetLab()
        self.SL.clear()

        self.SL.set_boxProps(self.sim_X, self.sim_Y,
                             self.sim_X_N, self.sim_Y_N)
        self.SL.set_ABS_sweep(1, 5)

        self.SL.set_ports(self.cop_waveguide.connections, len(self.cop_waveguide.connections) * [PORT_TYPES.BOX_WALL])
        self.SL.send_polygons(self.cell, self.layer_ph)

        self.SL.start_simulation(wait=True)

        self.SL.release()


import numpy as np


class SimulationResult:
    def __init__(self):
        # structure is {"sweep_par_name":sweep_par_values_list}
        # simulation is intended to happen across tensor product
        # of all parameters
        self._swept_pars = OrderedDict()
        self.freqs = None
        self.sMatrices = None

    def set_swept_parameters(self, sweep_parameters):
        self._swept_pars = sweep_parameters

    def set_dimensions(self, freqs_N, ports_N):
        self.freqs = np.zeros(tuple(len(swept_par_list) for swept_par_list in self._swept_pars.values()) + (freqs_N,),
                              dtype=np.float64)
        self.sMatrices = np.zeros(
            tuple(len(swept_par_list) for swept_par_list in self._swept_pars.values()) + (freqs_N, ports_N, ports_N),
            dtype=np.complex128)

    def get_Sij(self, i, j):
        return self.sMatrices[..., i + 1, j + 1]


import numpy as np

### MAIN FUNCTION ###
if __name__ == "__main__":
    my_design = Sandbox('testScript')
    design_params_dict = OrderedDict([("dx", 0)])

    dx_vals = np.arange(-my_design.sim_X / 3, my_design.sim_X / 3, my_design.sim_X / 20)

    SR = SimulationResult()
    SR.set_swept_parameters({"dx": dx_vals})
    for i, dx in enumerate(dx_vals):
        my_design.dx = dx
        my_design.show()
        my_design.simulate()
        freqs, sMatrices = my_design.SL.get_s_params()
        if i == 0:
            SR.set_dimensions(len(freqs), sMatrices.shape[1])
        SR.freqs[i] = freqs
        SR.sMatrices[i] = sMatrices

    with open(r"C:\Users\user\Documents\Sandbox\KLayout\SimRes.pkl", "wb") as f:
        pkl.dump(SR, f)

    # my_design.save_as_gds2(r'C:\Users\andre\Documents\chip_designs\chip_design.gds2')