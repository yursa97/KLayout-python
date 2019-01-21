import pya
from math import sqrt, cos, sin, atan2, pi, copysign
from pya import Point,DPoint,DSimplePolygon,SimplePolygon, DPolygon, Polygon,  Region
from pya import Trans, DTrans, CplxTrans, DCplxTrans, ICplxTrans

from importlib import reload

from .BaseClasses import Complex_Base
from .Coplanars import CPW_RL_Path, CPW
from .Coplanars import Coil_type_1, CPW_arc # backward compatibility TODO: delete classes

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
                The point where the resonator's coupling tail ends
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
        
        meander_length = (self._length - self._coupling_length \
            - self._offset_length - 2*2*pi*R/4 \
            -N*2*pi*R - 2*pi*R/2 + R - 2*pi*R/4 - self._neck_length)/(2*N+3/2)
        shape = "LRLRL"+N*"RLRL"+"RLRL"
        segment_lengths = [self._coupling_length + R, self._offset_length + 2*R]\
             + [meander_length+R] + 2*N*[meander_length] \
             + [meander_length/2, self._neck_length+R]
        turn_angles = [pi/2, pi/2] + N*[-pi,pi]+[-pi, pi/2]
        
        line = CPW_RL_Path(self._origin, shape, 
            self._cpw_parameters, self._turn_radius, 
                segment_lengths, turn_angles, self._trans_in)
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

class CPWResonator2(Complex_Base):
    # neck doesn't stand out and instead spreads along the resonator
    _c = 299792458.0
    
    def __init__(self, origin, cpw_parameters, turn_radius, frequency, ɛ, 
        wavelength_fraction = 1/4, coupling_length = 200e3,
        meander_periods = 4, neck_length = 100e3, trans_in = None):
        """
        A CPW resonator of wavelength fraction with automatic length calculation
        from given frequency.

        Modification: with a neck along the resonator

        It is also possible to attach a primitive to the end of the resonator which
        should provide a get_phase_shift(   ) method to calculate its effective length
        as if it was just a straight CPW piece.

        Parameters:
            origin: DPoint
                The point where the resonator's coupling tail starts
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
                is not checked for consistency with the resonator's
                boundaries
            coupling_length: float
                The length of the segment parallel to the feedline
            meander_periods: int
                The number of periods in the meandering part
            neck_length: float
                The length of the straight part before the uncoupled end
                of the resonator
        """
        self.Z = cpw_parameters
        self.R = turn_radius
        self.cpl_L = coupling_length
        self.N = meander_periods
        self.neck = neck_length
        self.freq = frequency
        self.wavelength_fraction = wavelength_fraction
        self.eps = ɛ
        self.len = self._calculate_total_length()

        self.line = None # RL path that represents meandr
        self.open_end = None # open-ended coplanar at the and of the resonator

        super().__init__(origin, trans_in)

        self.start = self.line.connections[0]
        self.end = self.line.connections[1]
        self.alpha_start = self.line.angle_connections[0]
        self.alpha_end = self.line.angle_connections[1]
        
    def init_primitives(self):
        origin = DPoint(0, 0)
        meander_length = (self.len - self.cpl_L - (5 / 2 + 2 * self.N) * pi * self.R + 3 * self.R - self.neck) / (2 * self.N + 3 / 2)
        shape = "LRL" + self.N * "RLRL" + "RLRL"
        segment_lengths = [self.cpl_L, meander_length] + 2 * self.N * [meander_length] + [meander_length + 3 * self.R, self.neck]
        turn_angles = [pi] + self.N * [-pi, pi]+[-pi, -pi/2]
        
        self.line = CPW_RL_Path(origin, shape, self.Z, self.R, segment_lengths, turn_angles)
        self.primitives['line'] = self.line

        self.open_end = CPW(0, self.Z.b/2, self.line.end, self.line.end + DPoint(0, self.Z.b))
        self.primitives['open_end'] = self.open_end
        
    def _calculate_total_length(self):
        length = self._c / self.freq / sqrt(self.eps/2 + 0.5) / 1e9 * self.wavelength_fraction
        return length * 1e9 # in nm

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
        setattr(self, name, Coil_type_1(self.Z0, DPoint(0,0), self.L_coupling, self.r, self.L1) )
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
