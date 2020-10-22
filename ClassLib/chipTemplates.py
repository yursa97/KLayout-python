import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

import itertools

from ClassLib.baseClasses import ComplexBase
from ClassLib.shapes import Rectangle
from ClassLib.coplanars import CPWParameters
from ClassLib.contactPads import ContactPad


class Chip5x10_with_contactPads(ComplexBase):
    '''
    This object is implementing chip surface with 
    some default contact pads that are already present
    '''

    def __init__(self, origin, Z_params, trans_in=None):
        '''
        @params:
            origin: DPoint
                position of the left-buttom corner of the chip
            Z_params: Coplanars.CPWParameters class instance
                parameters (one value or an array of 8 values) of the coplanar waveguide used as inner end of the
                contact pads.
        '''
        self.chip_x = 10e6
        self.chip_y = 5e6
        self.center = DPoint(self.chip_x / 2, self.chip_y / 2)
        self.Z_params = [Z_params] * 8 if not isinstance(Z_params, list) else Z_params
        super().__init__(origin, trans_in)
        self.center = self.connections[-1]

    def init_primitives(self):
        origin = DPoint(0, 0)

        # drawing chip        
        self.chip = Rectangle(origin, self.chip_x, self.chip_y)
        self.primitives["chip"] = self.chip

        # contact pads
        self.contact_pad_left = ContactPad(origin + DPoint(0, self.chip_y / 2),
                                           {"w": self.Z_params[0].width, "g": self.Z_params[0].gap})
        self.primitives["cp_left"] = self.contact_pad_left

        self.contact_pad_right = ContactPad(origin + DPoint(self.chip_x, self.chip_y / 2),
                                            {"w": self.Z_params[1].width, "g": self.Z_params[1].gap},
                                            trans_in=Trans.R180)
        self.primitives["cp_right"] = self.contact_pad_right

        # top and bottom pads
        N_pads = 3
        self.connections = [self.contact_pad_left.end, self.contact_pad_right.end]
        self.angle_connections = [self.contact_pad_left.angle_connections[1],
                                  self.contact_pad_right.angle_connections[1]]

        self.contact_pads_top = [ContactPad(origin + DPoint(self.chip_x / (N_pads + 1) * (i + 1), self.chip_y),
                                            {"w": self.Z_params[2 + i].width, "g": self.Z_params[2 + i].gap},
                                            trans_in=Trans.R270) for i in range(0, N_pads)]
        for i in range(0, N_pads):
            self.primitives["cp_top_" + str(i)] = self.contact_pads_top[i]
            self.connections.append(self.contact_pads_top[i].end)
            self.angle_connections.append(self.contact_pads_top[i].angle_connections[1])

        self.contact_pads_bottom = [ContactPad(origin + DPoint(self.chip_x / (N_pads + 1) * (i + 1), 0),
                                               {"w": self.Z_params[5 + i].width, "g": self.Z_params[5 + i].gap},
                                               trans_in=Trans.R90) for i in range(0, N_pads)]
        for i in range(0, N_pads):
            self.primitives["cp_bot_" + str(i)] = self.contact_pads_bottom[i]
            self.connections.append(self.contact_pads_bottom[i].end)
            self.angle_connections.append(self.contact_pads_bottom[i].angle_connections[1])

        self.connections.append(DPoint(self.chip_x / 2, self.chip_y / 2))
        self.angle_connections.append(0)


class CHIP_10x10_12pads:
    """
    10x10 mm chip
    PCB design located here:
    https://drive.google.com/drive/folders/1TGjD5wwC28ZiLln_W8M6gFJpl6MoqZWF?usp=sharing
    """
    dx = 10e6
    dy = 10e6

    pcb_width = 260e3  # 0.26 mm
    pcb_gap = 190e3  # (0.64 - 0.26) / 2 = 0.19 mm
    pcb_feedline_d = 2500e3  # 2.5 mm
    pcb_Z = CPWParameters(pcb_width, pcb_gap)

    cpw_width = 24.1e3
    cpw_gap = 12.95e3
    chip_Z = CPWParameters(cpw_width, cpw_gap)

    @staticmethod
    def get_contact_pads():
        dx = CHIP_10x10_12pads.dx
        dy = CHIP_10x10_12pads.dy
        pcb_feedline_d = CHIP_10x10_12pads.pcb_feedline_d
        pcb_Z = CHIP_10x10_12pads.pcb_Z
        chip_Z = CHIP_10x10_12pads.chip_Z

        contact_pads_left = [
            ContactPad(
                DPoint(0, dy - pcb_feedline_d * (i + 1)), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3
            ) for i in range(3)
        ]

        contact_pads_bottom = [
            ContactPad(
                DPoint(pcb_feedline_d * (i + 1), 0), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3,
                trans_in=Trans.R90
            ) for i in range(3)
        ]

        contact_pads_right = [
            ContactPad(
                DPoint(dx, pcb_feedline_d*(i+1)), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3,
                trans_in=Trans.R180
            ) for i in range(3)
        ]

        contact_pads_top = [
            ContactPad(
                DPoint(dx - pcb_feedline_d * (i + 1), dy), pcb_Z, chip_Z, back_metal_width=50e3,
                back_metal_gap=100e3,
                trans_in=Trans.R270
            ) for i in range(3)
        ]

        # contact pads are ordered starting with top-left corner in counter-clockwise direction
        contact_pads = itertools.chain(
            contact_pads_left, contact_pads_bottom,
            contact_pads_right, contact_pads_top
        )

        return list(contact_pads)

    origin = DPoint(0, 0)
    box = pya.DBox(origin, origin + DPoint(dx, dy))

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
