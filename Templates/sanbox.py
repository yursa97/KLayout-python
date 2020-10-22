from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region, Box, DBox
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload

import сlassLib
reload(сlassLib)
from сlassLib import *

import sonnetSim
reload(sonnetSim)
from sonnetSim import SimulatedDesign, SonnetPort, PORT_TYPES, SimulationBox


class Sandbox(SimulatedDesign):
    def __init__(self, cell_name):
        super().__init__(cell_name)

        self.origin = DPoint(0, 0)
        self.Z = CPWParameters(20e3, 10e3)  # normal CPW
        self.Z_narrow = CPWParameters(10e3, 7e3)  # narrow CPW

        self.cop_waveguide = None

        ## SIMULATION PARAMETERS SECTION START ##
        self.sim_X = 0.5e6
        self.sim_Y = 0.2e6

        self.sim_X_N = 200
        self.sim_Y_N = 200
        ## SIMULATION PARAMETERS SECTION END ##

    # Call other methods drawing parts of the design from here
    def draw(self, design_params):
        self._design_params = design_params
        self.cell.clear()
        self.draw_sim_box(design_params)
        self.draw_waveguide(design_params)
        self.draw_square(design_params)

    def calculate_ports(self, design_params):
        port1 = SonnetPort(self.cop_waveguide.connections[0], PORT_TYPES.BOX_WALL)
        port2 = SonnetPort(self.cop_waveguide.connections[1], PORT_TYPES.BOX_WALL)
        self.ports = [port1, port2]

    def draw_sim_box(self, design_params):
        sim_box = Box(self.origin,
                      self.origin + DPoint(self.sim_X, self.sim_Y))
        self.region_ph.insert(sim_box)

    def draw_waveguide(self, design_params):
        self.cop_waveguide = CPW(cpw_params=self.Z,
                                 start=DPoint(0, self.sim_Y/2),
                                 end=DPoint(self.sim_X, self.sim_Y/2))
        self.cop_waveguide.place(self.region_ph)

    def draw_square(self, design_params):
        dx = design_params["square_dx"]
        p1 = DPoint(self.sim_X / 2 + dx, self.sim_Y / 2 - self.Z.width / 2 - self.Z.gap * 2 / 3)
        square = DBox(p1, p1 + DPoint(self.Z.b, self.Z.gap / 3))
        self.region_ph.insert(Box().from_dbox(square))

import numpy as np
### MAIN FUNCTION ###
if __name__ == "__main__":
    my_design = Sandbox('testScript')
    freqs = np.linspace(1e9, 5e9, 300)
    sim_box = SimulationBox(0.5e6, 0.2e6, 200, 200)
    my_design.set_fixed_parameters(freqs, simBox=sim_box)

    swept_params = {"square_dx": np.arange(-my_design.sim_X/3,my_design.sim_X/3,my_design.sim_X/20)}
    my_design.set_swept_parameters(swept_params)
    my_design.simulate_sweep()
    my_design.save_result()



