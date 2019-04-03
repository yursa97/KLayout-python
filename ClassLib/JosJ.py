import pya
from math import pi
from pya import DPoint,DSimplePolygon,SimplePolygon
from pya import Trans,DTrans,DVector,DPath

from ClassLib.BaseClasses import Element_Base, Complex_Base
from ClassLib.Shapes import Circle, Kolbaska
from ClassLib.Coplanars import CPWParameters, CPW, CPW_RL_Path

class AsymSquid(Complex_Base):
    '''
    Class to draw a symmetrical squid with outer positioning of the junctions.

    The notation 'length' is the dimension along the line which connects the contact pads,
    'width' is for the perpendicular direction.

    Parameters:
        pad_side: float
            A length of the side of triangle pad.
        (??) pad_r: float
            The radius of round angle of the contact pad.
        pads_distance:
            The distance between triangle contact pads.
        p_ext_width: float
            The width of curved rectangle leads which connect triangle contact pads and junctions.
        p_ext_r: float
            The angle radius of the pad extension
        sq_len: float
            The length of the squid, along leads.
        sq_width: float
            The total area of the squid.
            (does not count the reduction of area due to shadow angle evaporation).
        j_width: float
            The width of the upper small leads (straight) and also a width of the junction
        low_lead_w: float
            The width of the lower small bended leads before bending
        b_ext: float
            The extension of bended leads after bending
        j_length: float
            The length of the jj and the width of bended parts of the lower leads.
        n: int
            The number of angle in regular polygon which serves as a large contact pad
        bridge: float
            The value of the gap between two parts of junction in the design
        trans_in: Trans
            Initial transformation
    '''
    def __init__(self, origin, params, side=0, trans_in=None):
        # To draw only a half of a squid use 'side'
        # side = -1 is left, 1 is right, 0 is both (default)
        self.pad_side = params[0]
        self.pad_r = params[1]
        self.pads_distance = params[2]
        self.p_ext_width = params[3]
        self.p_ext_r = params[4]
        self.sq_len = params[5]
        self.sq_area = params[6]
        self.j_width = params[7]
        self.low_lead_w = params[8]
        self.b_ext = params[9]
        self.j_length_1 = params[10]
        self.j_length_2 = params[11]
        self.n = params[12]
        self.bridge = params[13]

        self.side = side

        super().__init__(origin, trans_in)


    def init_primitives(self):
        origin = DPoint(0,0)
        self._up_pad_center = origin + DVector(0,self.pads_distance/2)
        self._down_pad_center = origin + DVector(0,-self.pads_distance/2)
        self.primitives["pad_down"] = Circle(self._down_pad_center, self.pad_side, n_pts=self.n, offset_angle=pi/2)
        self.primitives["p_ext_down"] = Kolbaska(self._down_pad_center, origin + DVector(0,-self.sq_len/2),\
                                                self.p_ext_width,self.p_ext_r)
        self.primitives["pad_up"] = Circle(self._up_pad_center, self.pad_side, n_pts=self.n, offset_angle=-pi/2)
        self.primitives["p_ext_up"] = Kolbaska(self._up_pad_center, origin + DVector(0,self.sq_len/2),\
                                               self.p_ext_width,self.p_ext_r)
        if self.side == 0:
            self.init_half(origin, side=1) # right
            self.init_half(origin, side=-1) # left
        else:
            self.init_half(origin, side=self.side)

    def init_half(self, origin, side=-1):
        # side = -1 is left, 1 is right
        j_length = self.j_length_1 if side < 0 else self.j_length_2
        up_st_gap = self.sq_area / (2*self.sq_len)
        low_st_gap = up_st_gap + self.low_lead_w * 2.5
        up_st_start_p = self.primitives["p_ext_up"].connections[1]
        low_st_start_p = self.primitives["p_ext_down"].connections[1]
        
        up_st_start = up_st_start_p + DVector(side * up_st_gap/2, 0)
        up_st_stop = origin + DVector(side * up_st_gap/2, self.bridge/2)
        low_st_start = low_st_start_p + DVector(side * low_st_gap/2, 0)
        low_st_stop = origin + DVector(side * (low_st_gap/2 - self.b_ext), -self.bridge/2)
        Z_low = CPWParameters(j_length, 0)
        Z_low2 = CPWParameters(self.low_lead_w, 0)
        len_ly = (low_st_stop - low_st_start).y - Z_low2.width/2
        len_lb = side * (low_st_start - low_st_stop).x - Z_low2.width/2

        suff = "_left" if side < 0 else "_right"
        self.primitives["upp_st" + suff] = Kolbaska(up_st_start, up_st_stop, self.j_width, self.j_width/4)
        self.primitives["upp_st_thick" + suff] = Kolbaska(up_st_start,up_st_stop + DPoint(0, 2*self.bridge+self.low_lead_w/2), self.low_lead_w, self.low_lead_w/2)
        self.primitives["low_st" + suff] = CPW_RL_Path(low_st_start, 'LR', Z_low2, Z_low2.width/2,\
                                                    [len_ly],[side * pi/2],trans_in = DTrans.R90)
        self.primitives["low_st_jj" + suff] = CPW(Z_low.width, Z_low.gap, low_st_stop + DPoint(side * (self.b_ext - Z_low2.width/2),\
                                                 -j_length/2), low_st_stop + DPoint(0, -j_length/2))


class Squid(Complex_Base):
    '''
    Class to draw a symmetrical squid with outer positioning of the junctions.

    The notation 'length' is the dimension along the line which connects the contact pads,
    'width' is for the perpendicular direction.

    Parameters:
        pad_side: float
            A length of the side of triangle pad.
        (??) pad_r: float
            The radius of round angle of the contact pad.
        pads_distance:
            The distance between triangle contact pads.
        p_ext_width: float
            The width of curved rectangle leads which connect triangle contact pads and junctions.
        p_ext_r: float
            The angle radius of the pad extension
        sq_len: float
            The length of the squid, along leads.
        sq_width: float
            The total area of the squid.
            (does not count the reduction of area due to shadow angle evaporation).
        j_width: float
            The width of the upper small leads (straight) and also a width of the junction
        low_lead_w: float
            The width of the lower small bended leads before bending
        b_ext: float
            The extension of bended leads after bending
        j_length: float
            The length of the jj and the width of bended parts of the lower leads.
        n: int
            The number of angle in regular polygon which serves as a large contact pad
        bridge: float
            The value of the gap between two parts of junction in the design
        trans_in: Trans
            Initial transformation
    '''
    def __init__(self, origin, params, side=0, trans_in=None):
        # To draw only a half of a squid use 'side'
        # side = -1 is left, 1 is right, 0 is both (default)
        self.pad_side = params[0]
        self.pad_r = params[1]
        self.pads_distance = params[2]
        self.p_ext_width = params[3]
        self.p_ext_r = params[4]
        self.sq_len = params[5]
        self.sq_area = params[6]
        self.j_width = params[7]
        self.low_lead_w = params[8]
        self.b_ext = params[9]
        self.j_length = params[10]
        self.n = params[11]
        self.bridge = params[12]

        self.side = side

        super().__init__(origin, trans_in)


    def init_primitives(self):
        origin = DPoint(0,0)
        self._up_pad_center = origin + DVector(0,self.pads_distance/2)
        self._down_pad_center = origin + DVector(0,-self.pads_distance/2)
        self.primitives["pad_down"] = Circle(self._down_pad_center, self.pad_side, n_pts=self.n, offset_angle=pi/2)
        self.primitives["p_ext_down"] = Kolbaska(self._down_pad_center, origin + DVector(0,-self.sq_len/2),\
                                                self.p_ext_width,self.p_ext_r)
        self.primitives["pad_up"] = Circle(self._up_pad_center, self.pad_side, n_pts=self.n, offset_angle=-pi/2)
        self.primitives["p_ext_up"] = Kolbaska(self._up_pad_center, origin + DVector(0,self.sq_len/2),\
                                               self.p_ext_width,self.p_ext_r)
        if self.side == 0:
            self.init_half(origin, side=1) # right
            self.init_half(origin, side=-1) # left
        else:
            self.init_half(origin, side=self.side)

    def init_half(self, origin, side=-1):
        # side = -1 is left, 1 is right
        up_st_gap = self.sq_area / (2*self.sq_len)
        low_st_gap = up_st_gap + self.low_lead_w * 2.5
        up_st_start_p = self.primitives["p_ext_up"].connections[1]
        low_st_start_p = self.primitives["p_ext_down"].connections[1]
        
        up_st_start = up_st_start_p + DVector(side * up_st_gap/2, 0)
        up_st_stop = origin + DVector(side * up_st_gap/2, self.bridge/2)
        low_st_start = low_st_start_p + DVector(side * low_st_gap/2, 0)
        low_st_stop = origin + DVector(side * (low_st_gap/2 - self.b_ext), -self.bridge/2)
        Z_low = CPWParameters(self.j_length, 0)
        Z_low2 = CPWParameters(self.low_lead_w, 0)
        len_ly = (low_st_stop - low_st_start).y - Z_low2.width/2
        len_lb = side * (low_st_start - low_st_stop).x - Z_low2.width/2

        suff = "_left" if side < 0 else "_right"
        self.primitives["upp_st" + suff] = Kolbaska(up_st_start, up_st_stop, self.j_width, self.j_width/4)
        self.primitives["upp_st_thick" + suff] = Kolbaska(up_st_start,up_st_stop + DPoint(0, 400), self.low_lead_w, self.low_lead_w/2)
        self.primitives["low_st" + suff] = CPW_RL_Path(low_st_start, 'LR', Z_low2, Z_low2.width/2,\
                                                    [len_ly],[side * pi/2],trans_in = DTrans.R90)
        self.primitives["low_st_jj" + suff] = CPW(Z_low.width, Z_low.gap, low_st_stop + DPoint(side * (self.b_ext - Z_low2.width/2),\
                                                 -self.j_length/2), low_st_stop + DPoint(0, -self.j_length/2))

class Line_N_JJCross(Element_Base):
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

        super().__init__( origin, trans_in )

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
