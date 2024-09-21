# For GPS WGS84 ellipsoidal height to above MSL height transition

from pyproj import CRS
from pyproj import Transformer

# Input CRS: WGS84(horizontal + vertical), global, used by GPS.
# EPSG 9754: WGS84(G2139), revision date: 2021-12-03
# This CRS is used by dashcam's GPS module. Should not modify.
_crs_in_epsg_id = 9754

# Output CRS: NAD83(horizontal) + NAVD88(vertical), North America only,
# NAVD88(orthometric height) can be used by Google Earth for elevtion.
# EPSG 5498: NAD83 + NAVD88, Revision date: 2011-03-29
# Change this CRS to your local CRS to have geoid data coverage.
crs_out_epsg_id = 5498

# CRS transition transformer
_t = Transformer.from_crs(
    CRS.from_epsg(_crs_in_epsg_id),
    CRS.from_epsg(crs_out_epsg_id)
)

# orthometric_height = ellipsoidal_height - geoid_height
# Geoid height is the height geoid above an ellipsoid
geoid_height = 0

def set_geoid_height(lat: float, lon: float):
    global geoid_height
    (lat1, lon1, geoid_height) = _t.transform(lat, lon, 0.0)
    geoid_height = -geoid_height

# Transform WGS84 ellipsoidal height to above MSL height
def get_elev(lat: float, lon: float, height: float) -> float:
    (lat1, lon1, h) = _t.transform(lat, lon, height)
    return h