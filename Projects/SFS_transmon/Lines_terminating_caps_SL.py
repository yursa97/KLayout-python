import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib import *

import sonnetSim
reload(sonnetSim)
from sonnetSim.sonnetLab import SonnetLab

import numpy as np
import csv
import os
import shutil

if( __name__ == "__main__" ):
    # getting main references of the appl

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
    cell_reg_photo = Region()

    # setting layout view  
    lv.select_cell(cell.cell_index(), 0)
    lv.add_missing_layers()
    
    ### DRAW SECTION START ###
    X_SIZE = 700e3
    Y_SIZE = 700e3
    
    # Box drwaing START #
    sonnet_box = pya.Box( 0,0, X_SIZE, Y_SIZE )
    #cell.shapes( layer_ph ).insert( sonnet_box )
    
    # Coplanar parameters
    width = 30e3
    gap = 0
    
    # CWave capacitor parameters#
    r_out = 200e3
    r_gap = 20e3
    r_in = r_out - r_gap
    n_semiwaves = 8
    s = 5e3  
    alpha = pi/2-0.1
    r_curve = 10e3
    n_pts_cwave = 50
    L0 = 20e3
    delta = 30e3 # displacement between circle halfs
    
    p0 = DPoint(sonnet_box.center())
    
    cwave_params = [r_out,r_gap,n_semiwaves,s,alpha,r_curve,delta,n_pts_cwave]
    cap = CWave( p0, *cwave_params, trans_in=Trans.R90 )
    cap.place(cell_reg_photo)
    
    overlap = 2e3
    
    Z_left = CPW(width, gap, DPoint(0, Y_SIZE/2), p0 + DPoint(-r_in + overlap, 0))
    Z_left.place(cell_reg_photo, merge=True)
    
    Z_right = CPW(width, gap, DPoint(X_SIZE, Y_SIZE/2), p0 + DPoint(r_in - overlap, 0))
    Z_right.place(cell_reg_photo, merge=True)
    ### DRAW SECTION END ###
    cell.shapes(layer_ph).insert(cell_reg_photo)
    lv.zoom_fit()


    ### SIMULATION SECTION START ###
    x_cells_N = 50
    y_cells_N = 50

    start_freq = 1
    stop_freq = 3

    SL = SonnetLab()
    SL.clear()

    SL.set_boxProps(X_SIZE,Y_SIZE, x_cells_N, y_cells_N)
    SL.set_ABS_sweep(start_freq, stop_freq)

    SL.send_cell_layer(cell, layer_ph, [Z_left.start, Z_right.start])

    SL.start_simulation(wait=True)
    print(SL.read_line())

    SL.visualize_sever()
    SL.release()
    ### SIMULATION SECTION END ###
    