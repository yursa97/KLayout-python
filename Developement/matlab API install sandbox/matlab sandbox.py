import socket
import sys
import time

import numpy as np
import struct

class Timer:    
    def __init__(self,sec, time_fcn=time.time):
        self.sec = sec
        self.p_time = 0
        self.time_fcn = time_fcn
        
        self.t_start = self.time_fcn()
        self.on = False
        self.last_interval = None
    
    def _update_time( self ):
        self.p_time = self.time_fcn() - self.t_start
    
    def start( self ):
        if( self.on is False ):
            self.t_start= self.time_fcn()
            self.on = True
        
    def stop( self ):
        if( self.on is True ):
            self._update_time()
            self.last_interval = self.p_time
            self.p_time = 0
            self.on = False
    
    def time( self ):
        if( self.on is True ):
            self._update_time()
            return self.p_time
        else:
            return self.last_interval
            
    def is_passed( self ):
        if( self.on is True ):
            return self.time() > self.sec
        elif( self.last_interval is not None ):
            return self.last_interval > self.sec
        else:
            return None

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
        print( "sending: ", byte_arr )
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
    
    def send_polygon( self, array_x, array_y, ports=False, port_edges_numbers_list=None ):
        self.send( CMD.POLYGON )
        
        if( ports is True ):
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
        
if( __name__ == "__main__"):
    writer = Matlab_commander()
    writer.send( CMD.SAY_HELLO )
    writer.send( CMD.CLEAR_POLYGONS )
    writer.send_boxProps( 100,100, 100,100 )
    writer.send_polygon( [0,0,100,100],[45,55,55,45], True, [1,3] )
    writer.send_set_ABS_sweep( 1, 10 )
    writer.send( CMD.SIMULATE )
    writer.send( CMD.CLOSE_CONNECTION )
    writer.close()
