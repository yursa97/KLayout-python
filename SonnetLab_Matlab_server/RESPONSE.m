classdef RESPONSE < uint16
    enumeration
        OK(0)
        ERROR(1)
        START_SIMULATION(2)
        BUSY_SIMULATION(3)
        SIMULATION_FINISHED(4)
    end
end