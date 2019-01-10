from pya import Point, DPoint, Vector, DVector, DSimplePolygon, SimplePolygon, DPolygon, Polygon, Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload

from ClassLib import *
reload(ClassLib)
from ClassLib import *

class Tshaped_Capacitor_Example(Chip_Design):
    origin = DPoint(0, 0)
    Z = CPWParameters(20e3, 10e3)  # normal CPW
    Z_narrow = CPWParameters(10e3, 7e3)  # narrow CPW
    cpw_curve = 200e3  # Curvature of CPW angles
    chip = None

    # Call other methods drawing parts of the design from here
    def draw(self):
        self.draw_Tshaped_capcitor()

    def draw_Tshaped_capacitor(self):
        raise NotImplemented

    def get_Tshaped_capacitor_parameter(self):
        raise NotImplemented




### MAIN FUNCTION ###
if __name__ == "__main__":
    my_design = Tshaped_Capacitor_Example('testScript')
    my_design.show()
    # my_design.save_as_gds2(r'C:\Users\andre\Documents\chip_designs\chip_design.gds2')