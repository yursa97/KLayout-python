import socket
import sys
import time

import numpy as np
import struct

import csv

import pya
from math import sqrt, cos, sin, tan, atan2, pi, copysign
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib.BaseClasses import Complex_Base
from ClassLib.Shapes import Rectangle
from ClassLib.ContactPad import Contact_Pad

class FLAG:
    FALSE = (0).to_bytes(2,byteorder="big")
    TRUE = (1).to_bytes(2,byteorder="big")

class CMD:
    SAY_HELLO = (0).to_bytes(2,byteorder="big")
    CLOSE_CONNECTION = (1).to_bytes(2,byteorder="big")
    FLOAT64_X1 = (2).to_bytes(2,byteorder="big")
    FLOAT64_XNUM = (3).to_bytes(2,byteorder="big")
    POLYGON = (4).to_bytes(2,byteorder="big")
    BOX_PROPS = (5).to_bytes(2,byteorder="big")
    CLEAR_POLYGONS = (6).to_bytes(2,byteorder="big")
    SET_ABS = (7).to_bytes(2,byteorder="big")
    SIMULATE = (8).to_bytes(2,byteorder="big")
    VISUALIZE = (9).to_bytes(2,byteorder="big")
    
class RESPONSE:
    OK = 0
    ERROR = 1

class Matlab_commander():
    MATLAB_PORT = 30000
    
    def __init__( self, host="localhost", port=MATLAB_PORT ):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.timeout = 10
        self.sock.settimeout( self.timeout )
        self.address = (host,port)
                
        try:
            self.sock.connect(self.address)
        except ConnectionRefusedError as e:
            print( "connection refused: ", e )
    
    def send( self, byte_arr ):
        confirm_byte = None
        #print( "sending: ", byte_arr )
        self.sock.sendall( byte_arr )
        
        # waiting for 1 byte received, timeout is 1 second
        try:
            confirm_byte = self.sock.recv(2)
            confirm_val = struct.unpack("!H",confirm_byte)[0]
            #print( "received: ", confirm_val==RESPONSE.OK )
        except Exception as e:
            print("exception on reception of confirm byte, following exception:")
            print(e)    
    
    def close(self):
        self.sock.close()
    
    def send_float64( self, val ):
        raw_data = struct.pack( ">d", np.float64(val) )
        self.send( raw_data )
        
    def send_array_float64( self, array ):
        raw_data = struct.pack( ">{0}d".format(len(array)), *array ) 
        self.send_uint32( len(array) )
        self.send( raw_data )
    
    def send_uint32( self, val ):
        raw_data = struct.pack( "!I", np.uint32(val) )
        self.send( raw_data )
    
    def send_array_uint32( self, array ):
        raw_data = struct.pack( "!{0}I".format(len(array)), *array ) 
        self.send_uint32( len(array) )
        self.send( raw_data )
    
    def send_polygon( self, array_x, array_y, port_edges_numbers_list=None ):
        self.send( CMD.POLYGON )
        
        if( port_edges_numbers_list is not None ):
            self.send( FLAG.TRUE )
            self.send_array_uint32( port_edges_numbers_list )
        else:
            self.send( FLAG.FALSE )
        
        self.send_array_float64( array_x )
        self.send_array_float64( array_y )
        
    def send_boxProps( self, dim_X_um, dim_Y_um, cells_X_num, cells_Y_num ):
        self.send( CMD.BOX_PROPS )
        self.send_float64( dim_X_um )
        self.send_float64( dim_Y_um )
        self.send_uint32( cells_X_num )
        self.send_uint32( cells_Y_num )
        
    def send_set_ABS_sweep(self, start_f, stop_f ):
        self.send( CMD.SET_ABS )
        self.send_float64( start_f )
        self.send_float64( stop_f )
        
    def read_line( self ):
        while( True ):
            data = self.sock.recv(1024,socket.MSG_PEEK)
            idx = data.find(b'\n')
            if( idx != - 1 ):
                data = self.sock.recv(idx+1)[:-1]
                break
            else:
                continue
                
        return data
            

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
    chip = Chip5x10_with_contactPads( origin, Z_params )
    chip.place( cell, layer_ph )
    # Chip drawing END #
    
    
    # Single photon source photo layer drawing START #
    r_out = 200e3
    r_gap = 25e3
    n_semiwaves = 4
    s = 5e3  
    alpha = pi/3
    r_curve = 10e3
    n_pts_cwave = 50
    L0 = 20e3
    delta = 30e3
    
    Z = CPW( cpw_params=Z_params )
    Z1 = Z
    d_alpha1 = pi/3
    width1 = r_gap/3 
    gap1 = width1
    Z2 = Z
    d_alpha2 = 2/3*pi
    width2 = width1
    gap2 = width2
    n_pts_arcs = 50
    sfs_params = [r_out, r_gap,n_semiwaves, s, alpha, r_curve, n_pts_cwave, L0, delta,
                        Z1,d_alpha1,width1,gap1,Z2,d_alpha2,width2,gap2, n_pts_arcs]
    
    Z3 = CPW( start = chip.connections[0], end = chip.connections[0] + DPoint( 0.5e6,0 ), cpw_params =  Z_params )
    Z3.place( cell, layer_ph )
    
    sfs = SFS_Csh_emb( Z3.end, sfs_params, trans_in=Trans.R90 )
    sfs.place( cell, layer_ph )
    
    r_curve = 0.2e6
    cpw_source_out = CPW_RL_Path( sfs.output, "LRL", Z_params, r_curve, 
                                                        [chip.connections[2].x - sfs.output.x, chip.connections[2].y-sfs.output.y],
                                                        [pi/2] )
    cpw_source_out.place( cell, layer_ph )
    # Single photon source  drawing END #
    
    # marks
    mark1 = Mark1( chip.center )
    mark1.place( cell, layer_ph )
    ### DRAW SECTION END ###
    
    lv.zoom_fit()
         
        
if( __name__ == "__main__"):
    writer = Matlab_commander()
    print("starting connection...")
    writer.send( CMD.SAY_HELLO )
    writer.send( CMD.CLEAR_POLYGONS )
    writer.send_boxProps( 100,100, 100,100 )
    writer.send_polygon( [0,0,100,100],[45,55,55,45], [1,3] )
    writer.send_set_ABS_sweep( 1, 10 )
    writer.send( CMD.SIMULATE )
    file_name = writer.read_line().decode("ASCII")
    print("visualizing...")
    writer.send( CMD.VISUALIZE )
    print("closing connection" )
    writer.send( CMD.CLOSE_CONNECTION )
    print("connection closed\n")
    writer.close()
    
    with open(file_name,"r") as csv_file:
        rows = np.array( list(csv.reader(csv_file))[8:], dtype=np.float64 )
