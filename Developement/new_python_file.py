# $description: Active script
# $version: 1
# $menu-path: My scripts
# $shortcut: Ctrl+E

# Enter your Python code here
import pya


from ClassLib import * 

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
    
layout = cv.layout()
layout.dbu = 0.001
if( layout.has_cell( "testScript") ):
    pass
else:
    cell = layout.create_cell( "testScript" )
    
    
info = pya.LayerInfo(1,0)
info2 = pya.LayerInfo(2,0)
layer_photo = layout.layer( info )
layer_el = layout.layer( info2 )

# clear this cell and layer
cell.clear()

# setting layout view  
lv.select_cell(cell.cell_index(), 0)
lv.add_missing_layers()

### DRAW SECTION START ###
cell.shapes( layer_photo ).insert( pya.Box( Point(0,0), Point( CHIP.dx, CHIP.dy ) ) )


p1 = DPoint(0,0)
p2 = DPoint( 10e3, 20e3)
width = 25e3
gap = 23e3
Z0 = CPW( width, gap, p1, p2 )

path = Path_RS(Z0, DPoint(0,1e6), DPoint(2e6,3e6))
path.place(cell, layer_photo)

rl_path_start = CPW_RL_Path(path.end, "RLR", [Z0], [100e3], 
      [100e3], [pi/2,-pi/2] ,trans_in = DCplxTrans(1, 90, True, 0,0))
rl_path_start.place(cell, layer_photo)

### DRAW SECTION END ###

lv.zoom_fit()