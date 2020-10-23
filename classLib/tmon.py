import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region, Instance, CellInstArray
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from classLib.baseClasses import *
from classLib.jJ import *

class Tmon(ElementBase):

    def __init__(self, origin, tmon_cpw_params, arms_len, JJ_arm_len, JJ_site_span,
                 coupling_pads_len, h_JJ, w_JJ, asymmetry, trans_in=None, use_cell=False):

        self.tmon_cpw_params = tmon_cpw_params
        self._arms_len = arms_len
        self._JJ_arm_len = JJ_arm_len
        self._JJ_site_span = JJ_site_span
        self._coupling_pads_len = coupling_pads_len
        self._h_JJ, self._w_JJ = h_JJ, w_JJ
        self._asymmetry = asymmetry
        self._use_cell = use_cell
        self._trans_in = trans_in
        self._origin = origin
        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]



    def init_regions(self):

        self.metal_regions["photo"] = Region()
        self.empty_regions["photo"] = Region()
        self.metal_regions["ebeam"] = Region()
        self.empty_regions["ebeam"] = Region()

        w_tmon, g_tmon = self.tmon_cpw_params.width, self.tmon_cpw_params.gap
        arms_len = self._arms_len
        JJ_arm_len = self._JJ_arm_len
        JJ_site_span = self._JJ_site_span

        coupling_pads_len = self._coupling_pads_len
        h_JJ, w_JJ = self._h_JJ, self._w_JJ
        asymmetry = self._asymmetry

        protect_points = [DPoint(0, 0),
                DPoint(-arms_len+g_tmon, 0),
                DPoint(-arms_len+g_tmon, -coupling_pads_len/2+w_tmon/2),
                DPoint(-arms_len-g_tmon-w_tmon, -coupling_pads_len/2+w_tmon/2),
                DPoint(-arms_len-g_tmon-w_tmon, coupling_pads_len/2+w_tmon/2+2*g_tmon),
                DPoint(-arms_len+g_tmon, coupling_pads_len/2+w_tmon/2+2*g_tmon),
                DPoint(-arms_len+g_tmon, 2*g_tmon+w_tmon),
                DPoint(-w_tmon/2-g_tmon, 2*g_tmon+w_tmon),
                DPoint(-w_tmon/2-g_tmon, g_tmon+w_tmon+JJ_arm_len+JJ_site_span),
                \
                DPoint(w_tmon/2+g_tmon, g_tmon+w_tmon+JJ_arm_len+JJ_site_span),
                DPoint(w_tmon/2+g_tmon, 2*g_tmon+w_tmon),
                DPoint(arms_len-g_tmon, 2*g_tmon+w_tmon),
                DPoint(arms_len-g_tmon, coupling_pads_len/2+w_tmon/2+2*g_tmon),
                DPoint(arms_len+g_tmon+w_tmon, coupling_pads_len/2+w_tmon/2+2*g_tmon),
                DPoint(arms_len+g_tmon+w_tmon, -coupling_pads_len/2+w_tmon/2),
                DPoint(arms_len-g_tmon, -coupling_pads_len/2+w_tmon/2),
                DPoint(arms_len-g_tmon, 0)]

        protect_region = Region(DSimplePolygon(protect_points))

        metal_points = [DPoint(0, g_tmon),
                DPoint(-arms_len, g_tmon),
                DPoint(-arms_len, g_tmon-coupling_pads_len/2+w_tmon/2),
                DPoint(-arms_len-w_tmon, g_tmon-coupling_pads_len/2+w_tmon/2),
                DPoint(-arms_len-w_tmon, g_tmon+coupling_pads_len/2+w_tmon/2),
                DPoint(-arms_len, g_tmon+coupling_pads_len/2+w_tmon/2),
                DPoint(-arms_len, g_tmon+w_tmon),
                DPoint(-w_tmon/2, g_tmon+w_tmon),
                DPoint(-w_tmon/2, g_tmon+w_tmon+JJ_arm_len),
                \
                DPoint(w_tmon/2, g_tmon+w_tmon+JJ_arm_len),
                DPoint(w_tmon/2, g_tmon+w_tmon),
                DPoint(arms_len, g_tmon+w_tmon),
                DPoint(arms_len, g_tmon+coupling_pads_len/2+w_tmon/2),
                DPoint(arms_len+w_tmon, g_tmon+coupling_pads_len/2+w_tmon/2),
                DPoint(arms_len+w_tmon, g_tmon-coupling_pads_len/2+w_tmon/2),
                DPoint(arms_len, g_tmon-coupling_pads_len/2+w_tmon/2),
                DPoint(arms_len, g_tmon)]

        metal_poly = DSimplePolygon(metal_points)
        self.metal_regions["photo"].insert(metal_poly)

        empty_region = protect_region - self.metal_regions["photo"]

        self.empty_regions["photo"].insert(empty_region)

        if not self._use_cell:

            squid = SQUIDManhattan(DPoint(0, g_tmon + w_tmon + JJ_arm_len + JJ_site_span / 2),
                                   self._w_JJ, self._h_JJ, \
                                   self._asymmetry, 150, JJ_site_span * 1.5, \
                                   squid_width_top=6.2e3, squid_width_bottom=4e3)

            self.metal_regions["ebeam"].insert(squid.metal_region)
        else:
            squid = SQUIDManhattan(DPoint(0, 0),
                                   self._w_JJ, self._h_JJ, \
                                   self._asymmetry, 150, JJ_site_span * 1.5, \
                                   squid_width_top=6.2e3, squid_width_bottom=4e3)
            # instance = Instance()
            # print(squid._cell.cell_index())
            trans = Trans(int(self._origin.x),
                          int(self._origin.y + g_tmon + w_tmon + JJ_arm_len + JJ_site_span / 2))
            arr = CellInstArray(squid._cell.cell_index(), trans)
            # print(arr.size())
            # instance.cell_inst = arr
            app = pya.Application.instance()
            cur_cell = app.main_window().current_view().active_cellview().cell
            cur_cell.insert(arr)

        self.connections = [DPoint(0,0),
                            DPoint(0, g_tmon+w_tmon+JJ_arm_len+JJ_site_span)]
