from collections import OrderedDict
from itertools import product

import numpy as np

from ClassLib.ChipDesign import Chip_Design
from .sonnetLab import SonnetLab

class SonnetPort:
    def __init__(self, point=None, port_type=None):
        self.point = point
        self.port_type = port_type

class SimulatedDesign(Chip_Design):
    def __init__(self, cell_name):
        super().__init__(cell_name)

        self.SL = SonnetLab() # matlab interface for simulating here
        
        # structure is {"sweep_par_name":sweep_par_values_list}
        # simulation is intended to happen across tensor product
        # of all parameters
        self._swept_pars = OrderedDict()

        # data storage references definition
        self.sMatrices = None  # np.array

        # fixed parameters definition
        self.freqs = None  # np.linspace(freq_start, freq_end, freqs_N)
        self.simulated_layer = self.layer_ph

        # ports are chamgimg with params
        self.ports = []  # list of SonnetPort class instances

    def supply_ports(self, **design_params):
        """
        virtual method
        """
        raise NotImplementedError

    def set_fixed_parameters(self, freqs,  simulated_layer=None):
        self.freqs = freqs
        if simulated_layer is not None:
            self.simulated_layer = simulated_layer  # by default it is self.layer_ph

    def set_swept_parameters(self, sweep_parameters):
        self._swept_pars = sweep_parameters

    def allocate_sMatrices(self):
        self.sMatrices = np.zeros(tuple(
            len(swept_par_list) for swept_par_list in self._swept_pars.values()
        )+(len(self.freqs), len(self.ports), len(self.ports)),
                                  dtype=np.complex128)

    def get_Sij(self, i, j):
        return self.sMatrices[..., i+1, j+1]

    def simulate_sweep(self):
        self.allocate_sMatrices()

        vals_prod = product(*self._swept_pars.values())
        vals_length_list = list(map(lambda x: len(x), list(self._swept_pars.values())))
        _idxs_iterables = [range(vals_length_list[i]) for i in range(len(self._swept_pars))]
        idxs_prod = product(*_idxs_iterables)

        for idxs, values in zip(idxs_prod, vals_prod):
            self.draw( OrderedDict([(key, val) for key, val in zip(self._swept_pars.keys(), values)]) )
            self.sMatrices[idxs] = self.simulate_design()

    def simulate_design(self):
        self.SL.clear()
        self.SL.set_boxProps(self.box_Props)
        # self.SL.set_ABS_sweep(self.freqs[0]/1e9, self.freqs[-1]/1e9)
        self.SL.set_linspace_sweep(self.freqs[0]/1e9, self.freqs[-1]/1e9, len(self.freqs))
        pts = []
        port_types = []
        for pt, port_type in self.ports:
            pts.append(pt)
            port_types.append(port_type)
        self.SL.set_ports(pts, port_types)

        self.SL.send_cell_layer(self.cell, self.simulated_layer)  # only 1 cell is supported
        self.SL.start_simulation(wait=True)
        self.SL.release()
        return self.SL.get_s_params()

    def save_result(self, path=None):
        import os
        import pickle as pkl
        if path is None:
            path = os.path.abspath(__file__)
        dirname = os.path.dirname(path)
        with open(os.join(dirname, "sim_res.pkl"), "wb") as o_file:
            pkl.dump(self, o_file)
