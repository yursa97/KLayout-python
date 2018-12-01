import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import *

class Contact_Pad(Element_Base):

    def __init__(self, origin, feedline_cpw_params, 
                 pad_cpw_params={"w":200e3, "g":120e3}, 
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
        
        w_pad, g_pad = self._pad_cpw_params["w"], self._pad_cpw_params["g"]
        w_feed, g_feed = self._feedline_cpw_params["w"], self._feedline_cpw_params["g"]
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
        self.angle_connections = [pi,0]
    
    
    
