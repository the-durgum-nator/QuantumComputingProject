import math

def _normalize_vector(x, y, z):
    """Normalize a vector to unit length"""
    length = math.sqrt(x*x + y*y + z*z)
    if length < 1e-10:
        return 0.0, 0.0, 0.0
    return x/length, y/length, z/length

def slerp_via_axis(start_x, start_y, start_z, end_x, end_y, end_z, t, via_vector=None):
    """
    Spherical linear interpolation via a specified direction.
    via_vector: tuple (x, y, z) - the direction to rotate through.
                For backward compatibility, can also be 'x', 'y', or 'z' string.
                If None, uses standard SLERP (shortest path).
    """
    
    # Normalize both vectors
    s_x, s_y, s_z = _normalize_vector(start_x, start_y, start_z)
    e_x, e_y, e_z = _normalize_vector(end_x, end_y, end_z)
    
    # Get the original magnitude
    start_mag = math.sqrt(start_x*start_x + start_y*start_y + start_z*start_z)
    end_mag = math.sqrt(end_x*end_x + end_y*end_y + end_z*end_z)
    
    if start_mag < 1e-10 or end_mag < 1e-10:
        # Linear interpolation for zero vectors
        return (start_x + (end_x - start_x) * t,
                start_y + (end_y - start_y) * t,
                start_z + (end_z - start_z) * t)
    
    # Compute dot product
    dot = s_x * e_x + s_y * e_y + s_z * e_z
    dot = max(-1.0, min(1.0, dot))  # Clamp for numerical stability
    
    # Check if vectors are nearly parallel or anti-parallel
    if abs(dot) > 0.9995:
        # For anti-parallel vectors, we need to find an intermediate point
        if dot < 0:  # Anti-parallel case
            # Use the specified via_vector or default to perpendicular
            if via_vector is None:
                # Find a perpendicular vector automatically
                if abs(s_x) < 0.9:
                    mid_x, mid_y, mid_z = _normalize_vector(0.0, -s_z, s_y)
                else:
                    mid_x, mid_y, mid_z = _normalize_vector(-s_y, s_x, 0.0)
            else:
                mid_x, mid_y, mid_z = _normalize_vector(via_vector[0], via_vector[1], via_vector[2])
            
            # Interpolate in two steps: start -> axis -> end
            if t < 0.5:
                # First half: interpolate from start to axis
                t_adjusted = t * 2.0
                return _slerp_standard(s_x, s_y, s_z, mid_x, mid_y, mid_z, t_adjusted, start_mag, start_mag)
            else:
                # Second half: interpolate from axis to end
                t_adjusted = (t - 0.5) * 2.0
                return _slerp_standard(mid_x, mid_y, mid_z, e_x, e_y, e_z, t_adjusted, end_mag, end_mag)
        else:
            # Nearly parallel, use linear interpolation
            return (start_x + (end_x - start_x) * t,
                    start_y + (end_y - start_y) * t,
                    start_z + (end_z - start_z) * t)
    
    # Standard SLERP
    return _slerp_standard(s_x, s_y, s_z, e_x, e_y, e_z, t, start_mag, end_mag)

def _slerp_standard(s_x, s_y, s_z, e_x, e_y, e_z, t, start_mag, end_mag):
    """Standard spherical linear interpolation"""
    dot = s_x * e_x + s_y * e_y + s_z * e_z
    dot = max(-1.0, min(1.0, dot))
    
    theta = math.acos(dot)
    sin_theta = math.sin(theta)
    
    if abs(sin_theta) < 1e-10:
        # Vectors are parallel
        result_mag = start_mag + (end_mag - start_mag) * t
        return s_x * result_mag, s_y * result_mag, s_z * result_mag
    
    a = math.sin((1.0 - t) * theta) / sin_theta
    b = math.sin(t * theta) / sin_theta
    
    result_mag = start_mag + (end_mag - start_mag) * t
    
    return ((a * s_x + b * e_x) * result_mag,
            (a * s_y + b * e_y) * result_mag,
            (a * s_z + b * e_z) * result_mag)