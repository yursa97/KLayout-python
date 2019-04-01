from collections import OrderedDict
from itertools import product

import numpy as np

from ClassLib.ChipDesign import Chip_Design
from .sonnetLab import SonnetLab

class SonnetPort:
    def __init__(self):
        self.pt = None
        self.type = None

class SimulatedDesign(Chip_Design):
    def __init__(self, cell_name):
        super().__init__()

        self.SL = SonnetLab() # matlab interface for simulating here
        
        # structure is {"sweep_par_name":sweep_par_values_list}
        # simulation is intended to happen across tensor product
        # of all parameters
        self._swept_pars = OrderedDict()

        # data storage references definition
        self.sMatrices = None  # np.array

        # fixed parameters definition
        self.freq_limits = None  # np.linspace(freq_start, freq_end, freqs_N)
        self.simulated_layer = self.layer_ph

        # ports are chamgimg with params
        self.ports = []  # list of SonnetPort class instances

    def place_ports(self):
        """
        virtual method
        """
        raise NotImplementedError

    def set_fixed_parameters(self, frequencies, ports,  simulated_layer=None):
        self.freqs = frequencies
        if( simulated_layer is not None ):
            self.simulated_layer = simulated_layer  # by default it is self.layer_ph

    def set_swept_parameters(self, sweep_parameters):
        self._swept_pars = sweep_parameters

    def allocate_sMatrices(self):
        self.sMatrices = np.zeros(tuple(len(swept_par_list) for swept_par_list in self._swept_pars.values())+(freqs_N,ports_N,ports_N),
                                   dtype=np.complex128)
    def get_Sij(self, i, j):
        return self.sMatrices[..., i+1, j+1]

    def simulate_sweep(self):
        self.allocate_sMatrices()

        vals_prod = product(*self._swept_pars.values())
        _idxs_iterables = [range(len(self._swept_pars.values()[i])) for i in len(self._swept_pars)]
        idxs_prod = product(*_idxs_iterables)

        for idxs, values in zip(idxs_prod, vals_prod):
            self.draw()
            self.sMatrices[idxs] = self.simulate_design()


    def simulate_design(self):
        self.SL.clear()
        self.SL.set_boxProps(self.box_Props)
        self.SL.set_ABS_sweep(self.freqs[0]/1e9, self.freqs[-1])

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