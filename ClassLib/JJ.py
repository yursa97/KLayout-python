import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import *
from ClassLib.Coplanars import *

class SQUIDManhattan(Complex_Base):

    def __init__(self, origin, w_JJ, h_JJ, asymmetry, bridge_width, structure_length,
        squid_width = 3e3, pad_width = 5e3, small_lead_width = .33e3,
        top_tiny_lead_length = 1e3, bottom_tiny_lead_length = 2e3,
        tiny_lead_outshoot = 1000, trans_in = None):

        self._w_JJ = w_JJ - 30
        self._h_JJ = h_JJ - 30
        self._asymmetry = asymmetry
        self._bridge_width = bridge_width + 15
        self._structure_length = structure_length
        self._squid_width = squid_width
        self._pad_width = pad_width
        self._small_lead_width = small_lead_width
        self._top_tiny_lead_length = top_tiny_lead_length
        self._bottom_tiny_lead_length = bottom_tiny_lead_length
        self._tiny_lead_outshoot = tiny_lead_outshoot

        super().__init__(origin, trans_in)

    def init_primitives(self):

        top_left_h_JJ = sqrt(1-self._asymmetry)*self._h_JJ
        top_right_h_JJ = sqrt(1+self._asymmetry)*self._h_JJ
        bottom_left_w_JJ = sqrt(1-self._asymmetry)*self._w_JJ
        bottom_right_w_JJ = sqrt(1+self._asymmetry)*self._w_JJ

        # Top

        cursor = DPoint(0, self._structure_length/2)
        self.primitives["top_pad"] =\
            CPW(self._pad_width, 0, cursor,
                cursor+DPoint(0, -self._structure_length/4))
        cursor = self.primitives["top_pad"].end

        cursor_l = cursor + DPoint(-self._squid_width/2-self._small_lead_width/2, 0)
        self.primitives["top_left_small_lead"] =\
            CPW(self._small_lead_width, 0, cursor_l,
                    cursor_l+DPoint(0, -self._structure_length/4+top_left_h_JJ/2))
        cursor_l = self.primitives["top_left_small_lead"].end

        cursor_l += DPoint(-self._small_lead_width/2, -top_left_h_JJ/2)
        self.primitives["top_left_tiny_lead"] =\
            CPW(top_left_h_JJ, 0, cursor_l,
                    cursor_l+DPoint(self._top_tiny_lead_length, 0))

        cursor_r = cursor + DPoint(self._squid_width/2+self._small_lead_width/2, 0)
        self.primitives["top_right_small_lead"] =\
            CPW(self._small_lead_width, 0, cursor_r,
                cursor_r+DPoint(0, -self._structure_length/4+top_right_h_JJ/2))
        cursor_r = self.primitives["top_right_small_lead"].end

        cursor_r += DPoint(self._small_lead_width/2, -top_right_h_JJ/2)
        self.primitives["top_right_tiny_lead"] =\
            CPW(top_right_h_JJ, 0, cursor_r,
                    cursor_r+DPoint(-self._top_tiny_lead_length, 0))


        # Bottom

        cursor = DPoint(0, -self._structure_length/2)
        self.primitives["bottom_pad"] =\
            CPW(self._pad_width, 0, cursor,
                cursor+DPoint(0, self._structure_length/4))
        cursor = self.primitives["bottom_pad"].end

        cursor_l = cursor +\
            DPoint(-self._squid_width/2 \
                    - self._small_lead_width*1.5 \
                    + self._top_tiny_lead_length + self._bridge_width\
                    + bottom_left_w_JJ, 0)
        self.primitives["bottom_left_small_lead"] =\
            CPW(self._small_lead_width, 0, cursor_l,
                cursor_l+DPoint(0, self._structure_length/4-self._bottom_tiny_lead_length+self._tiny_lead_outshoot))
        cursor_l = self.primitives["bottom_left_small_lead"].end

        cursor_l += DPoint(self._small_lead_width/2-bottom_left_w_JJ/2, 0)
        self.primitives["bottom_left_tiny_lead"] =\
            CPW(bottom_left_w_JJ, 0, cursor_l,
                cursor_l+DPoint(0, self._bottom_tiny_lead_length))

        cursor_r = cursor +\
            DPoint(self._squid_width/2 \
                    + self._small_lead_width*1.5 \
                    - self._top_tiny_lead_length - self._bridge_width\
                    - bottom_right_w_JJ, 0)
        self.primitives["bottom_right_small_lead"] =\
            CPW(self._small_lead_width, 0, cursor_r,
                cursor_r+DPoint(0, self._structure_length/4\
                                   -self._bottom_tiny_lead_length\
                                   +self._tiny_lead_outshoot))
        cursor_r = self.primitives["bottom_right_small_lead"].end

        cursor_r += DPoint(-self._small_lead_width/2+bottom_right_w_JJ/2, 0)
        self.primitives["bottom_right_tiny_lead"] =\
            CPW(bottom_right_w_JJ, 0, cursor_r,
                cursor_r+DPoint(0, self._bottom_tiny_lead_length))


class Line_N_JJCross( ElementBase ):
    def __init__( self, origin, params, trans_in=None  ):
        self.params = params
        self.a = params[0]
        self.b = params[1]
        self.jos1_b = params[2]
        self.jos1_a = params[3]
        self.f1 = params[4]
        self.d1 = params[5]
        self.jos2_b = params[6]
        self.jos2_a = params[7]
        self.f2 = params[8]
        self.d2 = params[9]
        self.w = params[10]

        self.poly1 = self._make_polygon( self.b, self.w, self.d1, self.f1,   self.d2 )

        super( Line_N_JJ,self ).__init__( origin, trans_in )

    def _make_polygon( self, length, w, d, f, overlapping ):
        polygon = DSimplePolygon
        p1 = DPoint(0,0)
        p2 = p1 + DPoint( length,0 )
        p3 = p2 + DPoint( 0, w )
        p4 = p3 - DPoint( overlapping,0 )
        p5 = p4 - DPoint( 0, d )
        p6 = p5 - DPoint( f,0 )
        p7 = p6 + DPoint( 0, d )
        p8 = p1 + DPoint( 0,w )

        polygon = DSimplePolygon( [p1,p2,p3,p4,p5,p6,p7,p8] )
        return polygon

    def init_regions( self ):
        self.metal_region.insert( SimplePolygon().from_dpoly( self.poly1 ) )
