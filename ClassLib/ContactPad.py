import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans, CellInstArray

from ClassLib.BaseClasses import *
from ClassLib.Coplanars import *
from ClassLib.JJ import *

class Contact_Pad(ElementBase):

    def __init__(self, origin, feedline_cpw_params,
                 pad_cpw_params=CPWParameters(200e3, 120e3),
                 pad_length=400e3, back_gap=120e3,
                 transition_len=150e3, ground_connector_width = 50e3,
                 trans_in = None):

        self._feedline_cpw_params = feedline_cpw_params
        self._pad_cpw_params = pad_cpw_params
        self._pad_length = pad_length
        self._back_gap = back_gap
        self._transition_length = transition_len
        self._ground_connector_width = ground_connector_width

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]



    def init_regions(self):

        w_pad, g_pad = self._pad_cpw_params.width, self._pad_cpw_params.gap
        w_feed, g_feed = self._feedline_cpw_params.width, self._feedline_cpw_params.gap
        x, y = self._ground_connector_width+self._back_gap, 0

        metal_points = [DPoint(x, y+w_pad/2),
                  DPoint(x+self._pad_length, y+w_pad/2),
                  DPoint(x+self._pad_length+self._transition_length, y+w_feed/2),
                  DPoint(x+self._pad_length+self._transition_length, y-w_feed/2),
                  DPoint(x+self._pad_length, y-w_pad/2),
                  DPoint(x, y-w_pad/2)]
        metal_poly = DSimplePolygon(metal_points)

        self.metal_region.insert(metal_poly)

        protect_points = [DPoint(x-self._back_gap, y+w_pad/2+g_pad),
                          DPoint(x+self._pad_length, y+w_pad/2+g_pad),
                          DPoint(x+self._pad_length+self._transition_length, y+w_feed/2+g_feed),
                          DPoint(x+self._pad_length+self._transition_length, y-w_feed/2-g_feed),
                          DPoint(x+self._pad_length, y-w_pad/2-g_pad),
                          DPoint(x-self._back_gap, y-w_pad/2-g_pad)]

        protect_poly = DSimplePolygon(protect_points)
        protect_region = Region(protect_poly)

        empty_region = protect_region - self.metal_region

        self.empty_region.insert(empty_region)


        self.connections = [DPoint(0,0), DPoint(x+self._pad_length+self._transition_length, 0)]


class Test_frame(ElementBase):

    def __init__(self, origin, w_JJ, h_JJ, asymmetry, JJ_site_span, frame_cpw_params=CPWParameters(200e3, 8e3),
                 frame_length=200e3, trans_in=None, use_cell=False):

        self._frame_cpw_params = frame_cpw_params
        self._frame_length = frame_length
        self._h_JJ, self._w_JJ = h_JJ, w_JJ
        self._asymmetry = asymmetry
        self._JJ_site_span = JJ_site_span
        self._use_cell = use_cell
        self._origin = origin

        super().__init__(origin, trans_in)

        self.start = self.connections[0]
        self.end = self.connections[1]

    def init_regions(self):

        self.metal_regions["photo"] = Region()
        self.empty_regions["photo"] = Region()
        self.metal_regions["ebeam"] = Region()
        self.empty_regions["ebeam"] = Region()

        w_frame, g_frame = self._frame_cpw_params.width, self._frame_cpw_params.gap
        l_frame = self._frame_length

        metal_points1 = [DPoint(g_frame, g_frame),
                         DPoint(g_frame + w_frame, g_frame),
                         DPoint(g_frame + w_frame, g_frame + l_frame),
                         DPoint(g_frame, g_frame + l_frame)]
        metal_poly1 = DSimplePolygon(metal_points1)

        self.metal_regions["photo"].insert(metal_poly1)

        metal_points2 = [DPoint(g_frame, 2 * g_frame + l_frame),
                         DPoint(g_frame + w_frame, 2 * g_frame + l_frame),
                         DPoint(g_frame + w_frame, 2 * g_frame + 2 * l_frame),
                         DPoint(g_frame, 2 * g_frame + 2 * l_frame)]
        metal_poly2 = DSimplePolygon(metal_points2)

        self.metal_regions["photo"].insert(metal_poly2)

        protect_points = [DPoint(0, 0),
                          DPoint(2 * g_frame + w_frame, 0),
                          DPoint(2 * g_frame + w_frame, 3 * g_frame + 2 * l_frame),
                          DPoint(0, 3 * g_frame + 2 * l_frame)]

        protect_poly = DSimplePolygon(protect_points)
        protect_region = Region(protect_poly)

        empty_region = protect_region - self.metal_regions["photo"]

        self.empty_regions["photo"].insert(empty_region)

        self.connections = [DPoint(0, 0), DPoint(g_frame + 0.5 * w_frame, 1.5 * g_frame + l_frame)]

        if not self._use_cell:

            squid = SQUIDManhattan(self.connections[1],
                                   self._w_JJ, self._h_JJ, \
                                   self._asymmetry, 150, self._JJ_site_span * 1.5, \
                                   squid_width_top=6.2e3, squid_width_bottom=4e3)

            self.metal_regions["ebeam"].insert(squid.metal_region)
        else:
            squid = SQUIDManhattan(DPoint(0, 0),
                                   self._w_JJ, self._h_JJ, \
                                   self._asymmetry, 150, self._JJ_site_span * 1.5, \
                                   squid_width_top=6.2e3, squid_width_bottom=4e3)
            # instance = Instance()
            # print(squid._cell.cell_index())
            trans = Trans(int(self._origin.x + g_frame + 0.5 * w_frame),
                          int(self._origin.y + 1.5 * g_frame + l_frame))
            arr = CellInstArray(squid._cell.cell_index(), trans)
            # print(arr.size())
            # instance.cell_inst = arr
            app = pya.Application.instance()
            cur_cell = app.main_window().current_view().active_cellview().cell
            cur_cell.insert(arr)
