# $description: Active script
# $version: 1
# $show-in-menu
# $menu-path: My scripts
# $shortcut: Ctrl+E

# Enter your Python code here
import pya


from ClassLib import * 


class Path_RS(Complex_Base):
    def __init__(self, Z0, start, end, trans_in=None):
        self.Z0 = Z0
        self.end = end
        self.dr = end - start
        super(Path_RS, self).__init__(start, trans_in)
        self.start = self.connections[0]
        self.end = self.connections[1]
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]

    def init_primitives(self):
        L = abs(abs(self.dr.y) - abs(self.dr.x))
        r = min(abs(self.dr.y), abs(self.dr.x))
        if(abs(self.dr.y) > abs(self.dr.x)):
            self.arc1 = CPW_arc(self.Z0, DPoint(0, 0), copysign(
                r, self.dr.y), copysign(pi/2, self.dr.x*self.dr.y))
            self.cop1 = CPW(self.Z0.width, self.Z0.gap, self.arc1.end,
                            self.arc1.end + DPoint(0, copysign(L, self.dr.y)))
            self.connections = [self.arc1.start, self.cop1.end]
            self.angle_connections = [self.arc1.alpha_start, self.cop1.alpha_end]
        else:
            self.cop1 = CPW(self.Z0.width, self.Z0.gap, DPoint(
                0, 0), DPoint(0, 0) + DPoint(copysign(L, self.dr.x), 0))
            self.arc1 = CPW_arc(self.Z0, self.cop1.end, copysign(
                r, self.dr.y), copysign(pi/2, self.dr.y*self.dr.x))
            self.connections = [ self.cop1.start, self.arc1.end]
            self.angle_connections = [ self.cop1.alpha_end,self.arc1.alpha_start]
            
        self.primitives = {"arc1": self.arc1, "cop1": self.cop1}



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