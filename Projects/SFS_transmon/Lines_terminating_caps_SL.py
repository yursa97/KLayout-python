import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point, DPoint, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from ClassLib import *
from sonnetLab.sonnetLab import SonnetLab

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

    # setting layout view  
    lv.select_cell(cell.cell_index(), 0)
    lv.add_missing_layers()
    
    ### DRAW SECTION START ###
    reg = Region()
    
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
    
    cwave_params = [r_out,r_gap,n_semiwaves,s,alpha,r_curve,delta,L0,n_pts_cwave]
    cap = CWave( p0, *cwave_params, trans_in=Trans.R90 )
    cap.place( cell, layer_ph )
    
    overlap = 2e3
    
    Z_left = CPW( width, gap, DPoint( 0, Y_SIZE/2 ), p0 + DPoint( -r_in + overlap ,0 ) )
    Z_left.place( cell, layer_ph, merge=True )
    
    Z_right = CPW( width, gap,DPoint( X_SIZE, Y_SIZE/2 ), p0 + DPoint( r_in - overlap ,0 ) )
    Z_right.place( cell, layer_ph, merge=True )
    ### DRAW SECTION START ###
    
    lv.zoom_fit()
    SL = SonnetLab()