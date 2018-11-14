import sys
import time

import csv

import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib import *
from sonnetLab.matlabClient import  MatlabClient

import numpy as np

class SonnetLab( MatlabClient ):
    def __init__(self, host="localhost", port=MatlabClient.MATLAB_PORT ):
        super(SonnetLab,self).__init__()
    
    def clear( self ):    
        self._clear()
        
    def set_boxProps( self, dim_X_um, dim_Y_um, cells_X_num, cells_Y_num ):
        self._set_boxProps( dim_X_um, dim_Y_um, cells_X_num, cells_Y_num )
        
    def set_ABS_sweep(self, start_f, stop_f ):
        self._set_ABS_sweep( start_f, stop_f )
    
    def send_element( self, el_class_obj ):
        el = el_class_obj # name alias
        
        if( el.metal_region.size() > 1 ):
            print( "region consists of more than 1 polygon, this is not supported yet")
            return None
        
        poly = el.metal_region[0].dup() # the only polygon in the region

        pts_x = np.zeros(poly.num_points(), dtype=np.int32 )
        pts_y = np.zeros(poly.num_points(), dtype=np.int32 )
        for i,p in enumerate(poly.each_point_hull()):
            pts_x[i] = p.x/1e3
            pts_y[i] = p.y/1e3
        
        self._send_polygon( pts_x,pts_y, el.sonnet_port_connection_indexes )
        
    def release( self ):
        print( "closing connection" )
        self._send( CMD.CLOSE_CONNECTION )
        print("connection closed\n")
        self._close()

if __name__ == "__main__":
# getting main references of the application
    app = pya.Application.instance()
    mw = app.main_window()
    lv = mw.current_view()
    cv = None
    
    #this insures that lv and cv are valid objects
    if( lv == None ):
        cv = mw.create_layout(1)
        lv = mw.current_view()
    else:
        cv = lv.active_cellview()

# find or create the desired by programmer cell and layer
    layout = cv.layout()
    layout.dbu = 0.001
    if( layout.has_cell( "testScript") ):
        pass
    else:
        cell = layout.create_cell( "testScript" )
    
    info = pya.LayerInfo(1,0)
    info2 = pya.LayerInfo(2,0)
    layer_ph = layout.layer( info )
    layer_el = layout.layer( info2 )

    # clear this cell and layer
    cell.clear()

    # setting layout view  
    lv.select_cell(cell.cell_index(), 0)
    lv.add_missing_layers()

    ### DRAW SECTION START ###
    origin = DPoint(0,0)
    
    # Chip drwaing START #
    Z_params = CPWParameters( 14.5e3, 6.7e3 ) 
    box = pya.Box( 0,0, 100e3,100e3 ) # 100x100 um box
    cell.shapes( layer_ph ).insert( box )
    
    cop = CPW( 14.5e3, 6.7e3, DPoint(0,50e3), DPoint(100e3,50e3) )
    cop.place( cell, layer_ph )
    cop.add_sonnet_port(0)
    cop.add_sonnet_port(1)
    ### DRAW SECTION END ###
    
    lv.zoom_fit()
    from sonnetLab.cMD import CMD
    ### MATLAB COMMANDER SECTION START ###
    ml_terminal = SonnetLab()
    print("starting connection...")
    ml_terminal._send( CMD.SAY_HELLO )
    ml_terminal.clear()
    ml_terminal.set_boxProps( 100,100, 100,100 )
    ml_terminal.send_element( cop )
    ml_terminal.set_ABS_sweep( 1, 10 )
    ml_terminal._send( CMD.SIMULATE )
    file_name = ml_terminal.read_line().decode("ASCII")
    print("visualizing...")
    ml_terminal._send( CMD.VISUALIZE )
    ml_terminal.release()
    
    with open(file_name,"r") as csv_file:
        rows = np.array( list(csv.reader(csv_file))[8:], dtype=np.float64 )
        
    ### MATLAB COMMANDER SECTION END ###
