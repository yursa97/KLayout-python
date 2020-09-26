classdef Polygon
    % represents Polygon object in 
    properties
        % float64 pts arrays that contains polygon points
        points_x % x coordinates of points
        points_y % y coordinates of points
        ports % bool variable that specifies, whether this polygon has to be attached with any kind of port
        % if "ports" is True -> this list contains number of edges (starting with 0) that should be
        % attached with the port
        port_types % array PORT_TYPES instances that specifies port type.
        port_edges_num_list
    end
end

