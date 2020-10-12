import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

import math

from ClassLib.BaseClasses import Complex_Base
from ClassLib.Coplanars import CPWParameters, CPW, CPW2CPW

class ContactPad(Complex_Base):
    def __init__(self, origin, pcb_cpw_params=CPWParameters(width=200e3, gap=120e3),
                 chip_cpw_params=CPWParameters(width=24.1e3, gap=12.95e3),
                 pad_length=300e3, back_metal_width=0, back_metal_gap=None,
                 transition_len=150e3,
                 trans_in=None):

        self.pcb_cpw_params: CPWParameters = pcb_cpw_params
        self.chip_cpw_params: CPWParameters = chip_cpw_params
        self.pad_length = pad_length
        self.back_metal_length = back_metal_width
        if back_metal_gap is not None:
            self.back_metal_gap = back_metal_gap
        else:
            self.back_metal_gap = self.pcb_cpw_params.gap
        self.transition_length = transition_len

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]

    def init_primitives(self):
        origin = DPoint(0, 0)

        # place metal between pad and PCB-chip edge
        self.cpw_back_metal = CPW(
            self.pcb_cpw_params.b, 0,
            start=origin, end=origin + DPoint(self.back_metal_length, 0)
        )
        self.primitives["cpw_back_metal"] = self.cpw_back_metal

        # erase metal between previous metal structure and pad-pcb face
        self.cpw_back_gap = CPW(
            0, self.pcb_cpw_params.b / 2,
            start=self.cpw_back_metal.end,
            end=self.cpw_back_metal.end + DPoint(self.back_metal_gap, 0)
        )
        self.primitives["cpw_back_gap"] = self.cpw_back_gap

        # place PCB-matching pad
        self.cpw_pcb_match = CPW(
            start=self.cpw_back_gap.end,
            end=self.cpw_back_gap.end + DPoint(self.pad_length, 0),
            cpw_params=self.pcb_cpw_params
        )
        self.primitives["cpw_pcb_match"] = self.cpw_pcb_match

        # PCB-match to on-chip waveguide trapeziod adapter
        self.cpw2cpw = CPW2CPW(
            self.pcb_cpw_params,
            self.chip_cpw_params,
            start=self.cpw_pcb_match.end,
            end=self.cpw_pcb_match.end + DPoint(self.transition_length, 0)
        )
        self.primitives["cpw2cpw"] = self.cpw2cpw

        self.connections = [origin, self.cpw2cpw.end]
        self.angle_connections = [0, self.cpw2cpw.alpha_end]
