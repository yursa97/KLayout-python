# script id: 1

import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib import * 

import numpy as np
import csv
import os
import shutil

SIMULATION_ID = "Cwave_first"
SONNET_DIR = r"C:\Users\user\Documents\CWave_capacitance_simulations"
    
# Enter your Python code here
### MAIN FUNCTION ###
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
    
    # drawing ports
    gap = 0
    width = 30e3
    length = 150e3
    delta = 10e3
    
    # CWave capacitor drawing START #
    r_out = 200e3
    r_gap = 0
    n_semiwaves = 8
    s = 5e3  
    alpha = pi/2-0.1
    r_curve = 10e3
    n_pts_cwave = 50
    L0 = 20e3
    delta = 30e3

    p0 = DPoint( r_out + length - delta, r_out*( 1 + 1/4 ) )
    # writing description file    
    with open( os.path.join(SONNET_DIR,SIMULATION_ID + ".csv"), "w" ) as csv_file:
        writer = csv.writer( csv_file )
        # header with parameters names
        writer.writerow( ["file_id, r_out","dr","n_semiwaves","s","alpha","r_curve","delta","L0","n_pts_cwave"] )
        
        # cycle that generates .GDS files and writes them on the "sonnet_dir" directory
        # also writing corresponding parameter rows to "sonnet_dir/desc_file.csv"
        for file_id,alpha in enumerate(np.linspace( 0,pi/2-0.1,5 )):
            Z_left = CPW( width, gap, p0 + DPoint( -r_out + delta,0 ), p0 + DPoint( -r_out - length + delta,0 ) )
            Z_left.place( cell, layer_ph, merge=True )
        
            Z_right = CPW( width, gap, p0 - DPoint( -r_out + delta,0 ), p0 - DPoint( -r_out - length + delta,0 ) )
            Z_right.place( cell, layer_ph, merge=True )
            
            cwave_params = [r_out,r_gap,n_semiwaves,s,alpha,r_curve,delta,L0,n_pts_cwave]
            cap = CWave( p0, *cwave_params, trans_in=Trans.R90 )
            cap.place( cell, layer_ph )
            
            layout.write( os.path.join( SONNET_DIR,SIMULATION_ID+ "_" + str(file_id) + ".gds" ) )
            cell.clear()
            writer.writerow( [file_id] + cwave_params )
        
    # copy generating script with its id to the sonnet directory
    shutil.copy2( __file__, SONNET_DIR )
    ### DRAW SECTION END ###
    
    lv.zoom_fit()