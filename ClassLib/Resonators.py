import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans


from ClassLib import *


class CPWResonator():
    
    _c = 299792458.0
    
    def __init__(self, origin, cpw_parameters, turn_radius, frequency, ɛ, 
        wavelength_fraction = 1/4, coupling_length = 200e3, offset_length = 200e3,
        meander_periods = 4, neck_length = 100e3, end_primitive = None, trans_in = None):
        '''
        A CPW resonator of wavelength fraction with automatic length calculation
        from given frequency.
        
        It's also possible to attach a primitive to the end of the resonator which
        should provide a get_phase_shift(   ) method to calculate it's effective length
        as if it was just a straight CPW piece.
        
        Parameters:
            origin: DPoint
                The point where the resonator's couling tail ends
                and the meander starts
            cpw_parameters: CPWParameters
                CPW parameters for the resonator
            turn_radius: float
                Raduis of the resonator's meander turns 
            frequency: float, GHz
                The frequency that the resonator will have
            ɛ: float
                Substrate relative permittivity
            wavelength_fraction: float
                The fraction of the wavelength the resonator's 
                fundamental mode has at resonance. This parameter
                is not checked for consistensy with the resonator's 
                boundaries
            coupling_length: float
                The length of the segment parallel to the feedline
            offset_length: float
                The distance away from the feedline before meandering
            meander_periods: int
                The number of periods in the meandering part
            neck_length: float
                The length of the straight part before the uncoupled end
                of the resonator
            end_primitive: Element_Base object
                Element that will be attached to the end of the resonator
        '''
        
        self._origin = origin
        self._cpw_parameters = cpw_parameters
        self._turn_radius = turn_radius
        self._coupling_length = coupling_length
        self._offset_length = offset_length
        self._meander_periods = meander_periods
        self._neck_length = neck_length
        self._frequency = frequency
        self._wavelength_fraction = wavelength_fraction
        self._ɛ = ɛ
        self._end_primitive = end_primitive
        self._length = self._calculate_total_length()
        self._trans_in = trans_in
        
        
    def place(self, cell, layer):
    
        N, R = self._meander_periods, self._turn_radius
        
        # meander_period = 2*meander_length + 2piR
        # self._length = coupling_length + (2piR/4 + offset_length + 2piR/4 + meander_length) 
        # + N*meander_period + 2piR/2 + (meander_length/2 - R) + 2piR/4 + neck_length
        
        meander_length = (self._length - self._coupling_length \
            - self._offset_length - 2*2*pi*R/4 \
            -N*2*pi*R - 2*pi*R/2 + R - 2*pi*R/4 - self._neck_length)/(2*N+3/2)
#        print(meander_length)
                             
        shape = "LRLRL"+N*"RLRL"+"RLRL"
        
        
        segment_lengths = [self._coupling_length + R, self._offset_length + 2*R]\
             + [meander_length+R] + 2*N*[meander_length] \
             + [meander_length/2, self._neck_length+R]
        
        turn_angles = [pi/2, pi/2] + N*[-pi,pi]+[-pi, pi/2]
        
#        print(sum([abs(turn_angle) for turn_angle in turn_angles])/pi)
#        print(sum(segment_lengths) +\
#             R*sum([abs(turn_angle) for turn_angle in turn_angles])-6*R)
#        print(self._length)
#        print(segment_lengths)
        
        line = CPW_RL_Path(self._origin, shape, 
            self._cpw_parameters, self._turn_radius, 
                segment_lengths, turn_angles, self._trans_in)
                
#        print(line.get_total_length())
#        print(line._segment_lengths)
        
        line.place(cell, layer)
        
        self.start = line.connections[0]
        self.end = line.connections[1]
        self.alpha_start = line.angle_connections[0]
        self.alpha_end = line.angle_connections[1]
        
        
    def _calculate_total_length(self):
        
        length = self._c/self._frequency/(sqrt(self._ɛ/2+0.5))/1e9*self._wavelength_fraction
        
        if self._end_primitive is not None:
            claw_phase_shift = self._claw.get_phase_shift(self._frequency)
            claw_effective_length = 1/180*claw_phase_shift/self._frequency/1e9*self._c/2/sqrt(self._ɛ/2+0.5)/2
            length -= claw_effective_length
            
        return length*1e9 # in nm
        
    
    

class EMResonator_TL2Qbit_worm( Complex_Base ):
    def __init__( self, Z0, start, L_coupling, L1, r, L2, N, trans_in=None ):
        self.Z0 = Z0
        self.L_coupling = L_coupling
        self.L1 = L1
        self.r = r
        self.L2 = L2

        self.N = N
        self.primitives_gnd = {}
        super().__init__( start, trans_in )

        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]
        
    def init_primitives( self ):
        name = "coil0"
        setattr(self,name, Coil_type_1(self.Z0, DPoint(0,0), self.L_coupling, self.r, self.L1) )
        self.primitives[name] = getattr( self, name )      
        # coils filling        
        for i in range(self.N):
            name = "coil" + str(i+1)
            setattr( self, name, Coil_type_1( self.Z0, DPoint( -self.L1 + self.L_coupling, -(i+1)*(4*self.r) ), self.L1, self.r, self.L1 ) )
            self.primitives[name] = getattr( self, name )
            
        # draw the "tail"
        self.arc_tail = CPW_arc( self.Z0, self.primitives["coil" + str(self.N)].end, -self.L1/2, -pi/2 )
        self.cop_tail = CPW( self.Z0.width, self.Z0.gap, self.arc_tail.end, self.arc_tail.end - DPoint( 0,self.L2 ) )
        self.cop_open_end = CPW( 0, self.Z0.b/2, self.cop_tail.end, self.cop_tail.end - DPoint(0,self.Z0.b) )
        self.primitives["arc_tail"] = self.arc_tail
        self.primitives["cop_tail"] = self.cop_tail
        self.primitives["cop_open_end"] = self.cop_open_end
        
        self.connections = [DPoint(0,0), self.cop_tail.end]
        self.angle_connections = [0,self.cop_tail.alpha_end]


class EMResonator_TL2Qbit_worm2( Complex_Base ):
    def __init__( self, Z0, start, L_coupling, L1, r, L2, N, trans_in=None ):
        self.Z0 = Z0
        self.L_coupling = L_coupling
        self.L1 = L1
        self.r = r
        self.L2 = L2

        self.N = N
        self.primitives_gnd = {}
        super().__init__( start, trans_in )

        self.start = self.connections[0]
        self.end = self.connections[-1]
        self.dr = self.end - self.start
        self.alpha_start = self.angle_connections[0]
        self.alpha_end = self.angle_connections[1]
        
    def init_primitives( self ):
        self.arc1 = CPW_arc( self.Z0, DPoint(0,0), -self.r, pi/2 )
        self.primitives["arc1"] = self.arc1
        
        # making coil
        name = "coil0"
        setattr(self,name, Coil_type_1(self.Z0, DPoint(0,0), self.L_coupling, self.r, self.L1) )
        self.primitives[name] = getattr( self, name )      
        # coils filling        
        for i in range(self.N):
            name = "coil" + str(i+1)
            setattr( self, name, Coil_type_1( self.Z0, DPoint( -self.L1 + self.L_coupling, -(i+1)*(4*self.r) ), self.L1, self.r, self.L1 ) )
            self.primitives[name] = getattr( self, name )
            
        # draw the "tail"
        self.arc_tail = CPW_arc( self.Z0, self.primitives["coil" + str(self.N)].end, -self.L1/2, -pi/2 )
        self.cop_tail = CPW( self.Z0.width, self.Z0.gap, self.arc_tail.end, self.arc_tail.end - DPoint( 0,self.L2 ) )
        self.cop_open_end = CPW( 0, self.Z0.b/2, self.cop_tail.end, self.cop_tail.end - DPoint(0,self.Z0.b) )
        self.primitives["arc_tail"] = self.arc_tail
        self.primitives["cop_tail"] = self.cop_tail
        self.primitives["cop_open_end"] = self.cop_open_end
        
        self.connections = [DPoint(0,0), self.cop_tail.end]
        self.angle_connections = [0,self.cop_tail.alpha_end]
