import pya
from pya import Region
from ClassLib import PROGRAM

from collections import OrderedDict

class Chip_Design:
    """ @brief:     inherit this class for working on a chip design
                    and override draw() method where other drawing
                    methods should be called from
                    call show() to draw everything
        @params:    str cell_name - name of a cell, e.g. 'testScript'
    """
    def __init__(self, cell_name):
        # getting main references of the application
        app = pya.Application.instance()
        mw = app.main_window()
        self.lv = mw.current_view()
        self.cv = None
        self.cell = None
        self.region_ph = Region()
        self.region_el = Region()
        
        #this insures that lv and cv are valid objects
        if(self.lv == None):
            self.cv = mw.create_layout(1)
            self.lv = mw.current_view()
        else:
            self.cv = self.lv.active_cellview()

        # find or create the desired by programmer cell and layer
        layout = self.cv.layout()
        layout.dbu = 0.001
        if(layout.has_cell(cell_name)):
            self.cell = layout.cell(cell_name)
        else:
            self.cell = layout.create_cell(cell_name)
        
        info = pya.LayerInfo(1,0)
        info2 = pya.LayerInfo(2,0)
        self.layer_ph = layout.layer(info) # photoresist layer
        self.layer_el = layout.layer(info2) # e-beam lithography layer

        # clear this cell and layer
        self.cell.clear()

        # setting layout view  
        self.lv.select_cell(self.cell.cell_index(), 0)
        self.lv.add_missing_layers()

        # current design parameters instance
        self.design_pars = OrderedDict()  # nested structure that contains device parameters for drawing
    
    # Call other methods drawing parts of the design from here
    def draw(self, **design_params):
        '''
        @brief: Purely virtual base-class method that is ought to be
                implemented in child classes.
                Responsible for calling functions that draw separate
                objects.
        '''
        raise NotImplementedError
    
    def __end_drawing(self):
        # this too methods assumes that all previous drawing
        # functions are placing their object on regions
        # in order to avoid extensive copying of the polygons
        # to/from cell.shapes during the logic operations on
        # polygons
        self.cell.shapes(self.layer_ph).insert(self.region_ph)
        self.cell.shapes(self.layer_el).insert(self.region_el)
        self.lv.zoom_fit()

    # Call this m
    def show(self, **design_params):
        self.draw(**design_params)
        self.__end_drawing()
    
    # Erases everything outside the box
    def select_box(self, box):
        self.__erase_in_layer(self.layer_ph, box)
        self.__erase_in_layer(self.layer_el, box)
    
    # Erases everything outside the box in a layer
    def __erase_in_layer(self, layer, box):
        r_cell = Region(self.cell.begin_shapes_rec(layer))
        emptyregion = Region(box)
        temp_i = self.cell.layout().layer(pya.LayerInfo(PROGRAM.LAYER1_NUM,0) ) 
        inverse_region = r_cell - emptyregion
        self.cell.shapes(temp_i).insert(r_cell - inverse_region)
        self.cell.layout().clear_layer(layer)
        self.cell.layout().move_layer(temp_i, layer)
        self.cell.layout().delete_layer(temp_i)
    
    # Save your design as GDS-II
    def save_as_gds2(self, filename):
        slo = pya.SaveLayoutOptions()
        slo.format = 'GDS2'
        slo.gds2_libname = 'LIB'
        slo.gds2_max_cellname_length = 32000
        slo.gds2_max_vertex_count = 8000
        slo.gds2_write_timestamps = True
        slo.select_all_layers()
        self.lv.save_as(self.cell.cell_index(), filename, slo)