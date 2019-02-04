import csv

import pya
from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from ClassLib import *
from .matlabClient import MatlabClient

import numpy as np

class SonnetLab( MatlabClient ):        
    def __init__(self, host="localhost", port=MatlabClient.MATLAB_PORT ):
        super(SonnetLab,self).__init__()
        self.state = self.STATE.READY

        # file that stores results of the last successful simulation
        self.sim_res_file = None
        self.ports = None
        self.ports_types = None # ports types array of PORT_TYPES class instances
        self.freqs = None
        self.sMatrices = None
    
    def clear( self ):    
        self._clear()
        
    def set_boxProps( self, dim_X_nm, dim_Y_nm, cells_X_num, cells_Y_num ):
        self._set_boxProps( dim_X_nm/1e3, dim_Y_nm/1e3, cells_X_num, cells_Y_num )
        
    def set_ABS_sweep(self, start_f_GHz, stop_f_GHz):
        self._set_ABS_sweep(start_f_GHz, stop_f_GHz)

    def set_ports(self, dpoint_array, ports_types):
        self.ports = dpoint_array
        self.ports_types = ports_types
        
    def send_polygon( self, polygon, port_edges_indexes=None, port_edges_types=None ):
        pts_x = np.zeros(polygon.num_points(), dtype=np.float64 )
        pts_y = np.zeros(polygon.num_points(), dtype=np.float64 )
        # print( "Sending polygon, edges: ", polygon.num_points_hull() )
        if port_edges_indexes is not None :
            print( "port edges indexes passing is not implemented yet." )
            raise NotImplemented
        else:
            port_edges_indexes = []
            port_edges_types = []

            for i, edge in enumerate(polygon.each_edge()):
                pts_x[i] = edge.p1.x/1.0e3
                pts_y[i] = edge.p1.y/1.0e3

                for port_i, conn_pt in enumerate(self.ports):
                    r_middle = (edge.p1 + edge.p2)*0.5
                    R = conn_pt.distance( r_middle )
                    if R < 10 : # distance from connection point to the middle of the edge <10 nm
                        port_edges_indexes.append(i+1) # matlab polygon edge indexing starts from 1
                        port_edges_types.append(self.ports_types[port_i]) # choosing appropriate port type
                        break

        self._send_polygon(pts_x, pts_y, port_edges_indexes, port_edges_types)
        
    def send_cell_layer(self, cell, layer_i):
        r_cell = Region(cell.begin_shapes_rec(layer_i))
        for poly in r_cell:
            self.send_polygon(poly.resolved_holes())
    
    def start_simulation(self, wait=True):
        '''
        @brief: function that start simulation on the remote matlab-sonnet server
        @params:
            bool wait - if True, the function blocks until simulation is over
                            if False, the function returns without waiting simulation results. 
                            Simulation status can be checked later using "get_simulation_status"
                            that performs non-blocking check of the simulation status
                            default value: True
        @return:
            bool - True if function has been terminated successfully
                      False otherwise          
        '''
        if( self.state != self.STATE.READY ):
            return
        # send simulation command
        self._send_simulate()

        if( wait == True ):
            while( self.state == self.STATE.BUSY_SIMULATING ):
                self.get_simulation_status() # updates self.state

        self.sim_res_file = self.read_line()
            
    def get_simulation_status( self ):
        self._get_simulation_status()
        return self.state

    def get_s_params(self):
        '''
        @brief: Function parses last csv file output from
                matlab. Works only in case if matlab server
                and sonnet server are executed at this machine.
        @return:    (freqs, sMatrices)
                    freqs : 1D numpy array of length freqs_N
                        stores simulation frequencies

                    sMatrices : 3D numpy array with shape (freqs_N, ports_N, ports_N)
                        ports_N - number of ports in the simulation
                        1st index - index of the frequency in freqs
                        2nd and 3rd indexes - row and column indexes
                        of the S-matrix that corresponds to the frequency
                        freq[1st index]
        '''
        if( self.sim_res_file is None ):
            print("sonnetLab.get_s_params: self.sim_res_file is None\n\
                   None is returned")
            return None

        data = None
        with open(self.sim_res_file, "r") as my_csv_file:
            data = np.array(list(csv.reader(my_csv_file))[8:], dtype=np.float64)
        freqs = np.array(data[:, 0], dtype=np.float64)
        s_data = np.array(data[:, 1::2] + 1j*data[:, 2::2], dtype=np.complex128)

        ports_N = len(self.ports)
        file_ports_N = int(round(np.sqrt(s_data.shape[1])))
        if( ports_N != file_ports_N ):
            print("sonnetLab.get_s_params(): internal ports number does not match\
                  file ports number,\nfile ports number:{}".format(file_ports_N))

        '''
        The original data is shaped as follows:
        0 - frequency index for example
        data[0] = [S11,S21,S31,...,Sn1, S21,S22,...,Sn2, ...,Snn]
        we want to reshape it to the following form:
        data[0] = [ [S11, S12, ..., S1n],
                    [S21, S22, ..., S2n],
                          ...          ,
                    [Sn1, Sn2, ..., Snn] ]
        '''
        sMatrices = s_data.reshape((len(freqs), file_ports_N, file_ports_N)).transpose(0, 2, 1)
        return freqs, sMatrices

    def visualize_sever( self ):
        self._visualize_sever()
    
    def release(self):
        # print("closing connection...")
        self._close()
        # print("connection closed\n")

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
    
    X_SIZE = 100e3
    Y_SIZE = 100e3
    
    # Chip drwaing START #
    cpw_pars = CPWParameters( 14.5e3, 6.7e3 ) 
    box = pya.Box( 0,0, X_SIZE,Y_SIZE )
    cell.shapes( layer_ph ).insert( box )
    
    cop = CPW_RL_Path( DPoint(0,Y_SIZE/2), "LRL", cpw_pars, 10e3, [X_SIZE/2,Y_SIZE/2], np.pi/2 )
    cop.place( cell, layer_ph )
    ports = [cop.start, cop.end]
    ### DRAW SECTION END ###
    
    lv.zoom_fit()
    from sonnetLab.cMD import CMD
    ### MATLAB COMMANDER SECTION START ###
    ml_terminal = SonnetLab()
    print("starting connection...")
    ml_terminal._send( CMD.SAY_HELLO )
    ml_terminal.clear()
    ml_terminal.set_boxProps( X_SIZE,Y_SIZE, 300,300 )
    print( "sending cell and layer" )
    ml_terminal.send_cell_layer( cell, layer_ph, ports )
    ml_terminal.set_ABS_sweep( 1, 10 )
    print( "simulating..." )
    ml_terminal.start_simulation( wait=True )
    print("visualizing...")
    ml_terminal.visualize_sever()
    file_name = ml_terminal.read_line()#.decode("ASCII")
    ml_terminal.release()

    with open(file_name,"r") as csv_file:
        rows = np.array( list(csv.reader(csv_file))[8:], dtype=np.float64 )
        
    ### MATLAB COMMANDER SECTION END ###
