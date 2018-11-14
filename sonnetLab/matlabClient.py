import socket
import struct
import numpy as np

from .cMD import CMD
from .flags import FLAG, RESPONSE

class MatlabClient():
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
    
    def _send( self, byte_arr ):
        confirm_byte = None
        #print( "sending: ", byte_arr )
        self.sock.sendall( byte_arr )
        
        # waiting for 2 confirmation bytes received or timeout expired
        try:
            confirm_byte = self.sock.recv(2)
            confirm_val = struct.unpack("!H",confirm_byte)[0]
            #print( "received: ", confirm_val==RESPONSE.OK )
        except Exception as e:
            print("exception on reception of confirm byte, following exception:")
            print(e)    
    
    def _close(self):
        self.sock.close()
    
    def _send_float64( self, val ):
        raw_data = struct.pack( ">d", np.float64(val) )
        self._send( raw_data )
        
    def _send_array_float64( self, array ):
        raw_data = struct.pack( ">{0}d".format(len(array)), *array ) 
        self._send_uint32( len(array) )
        self._send( raw_data )
    
    def _send_uint32( self, val ):
        raw_data = struct.pack( "!I", np.uint32(val) )
        self._send( raw_data )
    
    def _send_array_uint32( self, array ):
        raw_data = struct.pack( "!{0}I".format(len(array)), *array ) 
        self._send_uint32( len(array) )
        self._send( raw_data )
        
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
        
    def _send_polygon( self, array_x, array_y, port_edges_numbers_list=None ):
        self._send( CMD.POLYGON )
        
        if( port_edges_numbers_list is not None ):
            self._send( FLAG.TRUE )
            self._send_array_uint32( port_edges_numbers_list )
        else:
            self._send( FLAG.FALSE )
        
        self._send_array_float64( array_x )
        self._send_array_float64( array_y )
        
    def _set_boxProps( self, dim_X_um, dim_Y_um, cells_X_num, cells_Y_num ):
        self._send( CMD.BOX_PROPS )
        self._send_float64( dim_X_um )
        self._send_float64( dim_Y_um )
        self._send_uint32( cells_X_num )
        self._send_uint32( cells_Y_num )
        
    def _set_ABS_sweep(self, start_f, stop_f ):
        self._send( CMD.SET_ABS )
        self._send_float64( start_f )
        self._send_float64( stop_f )
        
    def _clear( self ):
        self._send( CMD.CLEAR_POLYGONS )