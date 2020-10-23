import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from classLib.baseClasses import *

class FluxCoil(ElementBase):

    def __init__(self, origin, fc_cpw_params, width = 5e3, trans_in = None):

        self._fc_cpw_params = fc_cpw_params
        self._width = width

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]


    def init_regions(self):

        w_fc, g_fc = self._fc_cpw_params.width, self._fc_cpw_params.gap

        empty_points = [DPoint(w_fc/2, 0),
                DPoint(w_fc/2, w_fc),
                DPoint(-self._width/2, w_fc),
                DPoint(-self._width/2, w_fc+g_fc),
                DPoint(self._width/2, w_fc+g_fc),
                DPoint(self._width/2, w_fc),
                DPoint(w_fc/2+g_fc, w_fc),
                DPoint(w_fc/2+g_fc, 0)]

        empty_region = Region(DSimplePolygon(empty_points))
        self.empty_region.insert(empty_region)

        self.connections = [DPoint(0,0), DPoint(0, w_fc+g_fc)]
