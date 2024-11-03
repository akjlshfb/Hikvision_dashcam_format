# For GPS WGS84 ellipsoidal height to above MSL height transition
try:
    from pyproj import CRS
    from pyproj import Transformer
    from pyproj import Geod
    has_pyproj = True
except ImportError:
    # Pyproj is not installed
    has_pyproj = False

# Input CRS: WGS84(horizontal + vertical), global, used by GPS.
# EPSG 9754: WGS84(G2139), revision date: 2021-12-03
# This CRS is used by dashcam's GPS module. Should not modify.
__crs_in_epsg_id = 9754

# Cartesian 3D coordination system. Use XYZ axis.
__crs_in_xyz_espg_id = 9753

# Output CRS: NAD83(horizontal) + NAVD88(vertical), North America only,
# NAVD88(orthometric height) can be used by Google Earth for elevtion.
# EPSG 5498: NAD83 + NAVD88, Revision date: 2011-03-29
# Change this CRS to your local CRS to have geoid data coverage.
crs_out_epsg_id = 5498

# CRS transition transformer
__t = Transformer.from_crs(
    CRS.from_epsg(__crs_in_epsg_id),
    CRS.from_epsg(crs_out_epsg_id)
) if has_pyproj else None

# XYZ and lat lon height system transformrs
__t_latlon_to_xyz = Transformer.from_crs(
    CRS.from_epsg(__crs_in_epsg_id),
    CRS.from_epsg(__crs_in_xyz_espg_id)
) if has_pyproj else None
__t_xyz_to_latlon = Transformer.from_crs(
    CRS.from_epsg(__crs_in_xyz_espg_id),
    CRS.from_epsg(__crs_in_epsg_id)
) if has_pyproj else None
__t_xyz_to_latlonelev = Transformer.from_crs(
    CRS.from_epsg(__crs_in_xyz_espg_id),
    CRS.from_epsg(crs_out_epsg_id)
) if has_pyproj else None

# orthometric_height = ellipsoidal_height - geoid_height
# Geoid height is the height geoid above an ellipsoid
geoid_height = 0

def set_geoid_height(lat: float, lon: float):
    global geoid_height
    if has_pyproj:
        (lat1, lon1, geoid_height) = __t.transform(lat, lon, 0.0)
        geoid_height = -geoid_height
    else:
        print('Error: Pyproj is not installed. You should directly set geoid height.')
        exit()

# Transform WGS84 ellipsoidal height to above MSL height
def get_elev(lat, lon, height) -> float:
    if has_pyproj:
        (lat1, lon1, h) = __t.transform(lat, lon, height)
        return h
    else:
        # orthometric_height = ellipsoidal_height - geoid_height
        global geoid_height
        return (height - geoid_height)

def t_latlon_to_xyz(lat, lon, height) -> tuple:
    """
    Transform from latitude longtitude ellipsoidal height to
    XYZ coordination system.

    Returns
    ----------
    tuple(x, y, z)
    """
    if has_pyproj:
        return __t_latlon_to_xyz.transform(lat, lon, height)
    else:
        #TODO: Manually transform
        print('Error: not implemented.')
        exit()

def t_xyz_to_latlon(x, y, z) -> tuple:
    """
    Transform from XYZ to latitude longtitude
    ellipsoidal height coordination system.

    Returns
    ----------
    tuple(lat, lon, height)
    """
    if has_pyproj:
        return __t_xyz_to_latlon.transform(x, y, z)
    else:
        #TODO: Manually transform
        print('Error: not implemented.')
        exit()

def t_xyz_to_latlonelev(x, y, z) -> tuple:
    """
    Transform from XYZ to latitude longtitude
    above mean sea level height coordination system.

    Returns
    ----------
    tuple(lat, lon, height)
    """
    if has_pyproj:
        return __t_xyz_to_latlonelev.transform(x, y, z)
    else:
        #TODO: Manually transform
        print('Error: not implemented.')
        exit()

def calc_heading(lat1, lon1, lat2, lon2, distance_threshold: float = 2.0):
    """
    Calculate heading FROM point 1 TO point 2.

    Parameters
    ----------
    lat1: list
        Latitude of point 1
    lon1: list
        Longtitude of point 1
    lat2: list
        Latitude of point 2
    lon2: list
        Longtitude of point 2
    distance_threshold: float
        If distance between point 1 and 2 is less than the
        threshold, previous heading value will be used.

    Returns
    ----------
    heading
    """
    if has_pyproj:
        geod = Geod(ellps = 'WGS84')
        result = geod.inv(lon1, lat1, lon2, lat2)
        heading = result[0]
        distance = result[2]
        for i in range(1, len(heading)):
            if distance[i] < distance_threshold:
                heading[i] = heading[i - 1]
        return heading
    else:
        #TODO: Manually transform
        print('Error: not implemented.')
        exit()
