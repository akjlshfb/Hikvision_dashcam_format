from datetime import datetime

import common
import geoid

# Whether to use a single uniformed geoid height to calc elev
use_uniform_geoid_height = False

geojson_indent = 2

#===========================================

def set_geoid_height_pyproj(telemetries: list):
    """
    Use pyproj to calculate geoid height in the first point in telemetry.

    Parameters
    ----------
    telemetries: list
        Telemetries get from parse_video.parse_videos(). See README.md

    Returns
    ----------
    Nothing
    """
    # Use first point in first track segment to determine geoid height
    geoid.set_geoid_height(
        telemetries[0]['telemetry']['gps_info']['gps_track'][0]['lat'] / 360000,
        telemetries[0]['telemetry']['gps_info']['gps_track'][0]['lon'] / 360000
    )

def set_geoid_height(geoid_height: float):
    """
    Directly set geoid height for GPS ellipsoidal height transform.

    Parameters
    ----------
    geoid_height: float
        Geoid height

    Returns
    ----------
    Nothing
    """
    # All transforms will use the same geoid height
    global use_uniform_geoid_height
    use_uniform_geoid_height = True
    # Use first point in first track segment to determine geoid height
    geoid.geoid_height = geoid_height

def __get_point_info(point: dict) -> tuple:
    """
    Convert units

    Parameters
    ----------
    point: dict
        parse_video.parse_seg()['gps_info']['gps_track'][]

    Returns
    ----------
    Tuple(
        time (datetime), 
        latitude (d), longtitude (d), 
        ellipsoidal height (m), above mean sea level height (m), geoid height (m),
        speed (m/s), heading (d)
    )
    """
    t = datetime.fromtimestamp(point['time'], tz = common.local_timezone)
    lat = point['lat'] / 360000 # centi sec to deg
    lon = point['lon'] / 360000 # centi sec to deg
    h = point['height'] / 100 # m
    if use_uniform_geoid_height: # height: cm ellisoidal to m amsl
        elev = h - geoid.geoid_height
        geoid_h = geoid.geoid_height
    else:
        elev = geoid.get_elev(
            lat, lon, h
        )
        geoid_h = h - elev
    speed = point['speed'] / 3.6 # km/h to m/s
    heading = point['heading']
    return (t, lat, lon, h, elev, geoid_h, speed, heading)

def export_geojson(
    geojson_file_path: str, telemetries: list,
    include_height: bool = True,
    use_amsl_height: bool = True
):
    """
    Export GPS data as GeoJSON file.

    Parameters
    ----------
    telemetries: list
        Result got from garse_video.parse_videos()
    include_height: bool
        True to create a 3D GPS track.
    use_amsl_height: bool
        Use above mean sea level height instead of GPS ellipsoidal height.

    Returns
    ----------
    Nothing
    """

    import json

    tracks = []
    for telemetry in telemetries:
        track = []
        for point in telemetry['telemetry']['gps_info']['gps_track']:
            (t, lat, lon, h, elev, geoid_h, speed, heading) = __get_point_info(point)
            height = elev if use_amsl_height else h
            if include_height:
                track.append([lon, lat, height])
            else:
                track.append([lon, lat])
        tracks.append(track)
    
    geojson = {}
    geojson['type'] = 'MultiLineString'
    geojson['coordinates'] = tracks

    with open(geojson_file_path, 'w+') as f:
        json.dump(geojson, f, indent = geojson_indent)

def export_gpx(gpx_file_path: str, telemetries: list):
    """
    Export GPS data as GPX file. GPX file version is '1.0'.

    Parameters
    ----------
    telemetries: list
        Result got from garse_video.parse_videos()

    Returns
    ----------
    Nothing
    """

    try:
        import gpxpy.gpx
    except ImportError:
        common.error('Module gpxpy is needed for GPX file export.')

    gpx = gpxpy.gpx.GPX()
    gpx.version = '1.0'

    track_no = 1
    parking_no = 1

    for telemetry in telemetries:
        if telemetry['telemetry']['parking']:
            point = telemetry['telemetry']['gps_info']['gps_track'][0]
            gpx_wpt = gpxpy.gpx.GPXWaypoint(name = f'Parking location {parking_no}')
            gpx.waypoints.append(gpx_wpt)
            (
                gpx_wpt.time,
                gpx_wpt.latitude,
                gpx_wpt.longitude,
                h,
                gpx_wpt.elevation,
                gpx_wpt.geoid_height,
                speed, heading
            ) = __get_point_info(point)
            desc_s = gpx_wpt.time.strftime('%Y-%m-%d %H:%M:%S UTC%z')
            gpx_wpt.description = 'Parking start at ' +  desc_s
            parking_no = parking_no + 1
        else:
            gpx_track = gpxpy.gpx.GPXTrack(name = f'Track {track_no}' )
            gpx.tracks.append(gpx_track)
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)
            gpx_points = []
            for point in telemetry['telemetry']['gps_info']['gps_track']:
                # if point['valid'] == 1:
                gpx_point = gpxpy.gpx.GPXTrackPoint()
                (
                    gpx_point.time,
                    gpx_point.latitude,
                    gpx_point.longitude,
                    h,
                    gpx_point.elevation,
                    gpx_point.geoid_height,
                    gpx_point.speed,
                    gpx_point.course
                ) = __get_point_info(point)
                gpx_points.append(gpx_point)
            gpx_segment.points = gpx_points
            desc_s = gpx_segment.points[0].time.strftime('%Y-%m-%d %H:%M:%S UTC%z')
            desc_e = gpx_segment.points[-1].time.strftime('%Y-%m-%d %H:%M:%S UTC%z')
            desc_l = gpx_segment.length_3d()
            desc = 'Track info\nStart: %s\nEnd: %s\nToltal length: %.3f km' % (desc_s, desc_e, desc_l / 1000)
            gpx_track.description = desc
            track_no = track_no + 1

    with open(gpx_file_path, 'w+') as f:
        f.write(gpx.to_xml(version = '1.0'))

def __interpolate_track(
    timestamp: list, lat: list, lon: list, h: list, points_per_gap: int
) -> tuple:
    """
    Interpolate GPS track with more points.

    Parameters
    ----------
    points_per_gap: int
        Points number to be added in each timestamp gap (1 second).

    Returns
    ----------
    tuple(time: list, lat: list, lon: list, elev: list, point_num: int)
        time is a list of datetime object.
        elev is a list of AMSL elevation height.
        point_num is the points number in the returned array.
    """

    try:
        import numpy as np
        from scipy.interpolate import CubicSpline
    except ImportError:
        common.error('Module simplekml is needed for GPS track point interpolation.')
    
    point_num = len(timestamp)
    # lat lon CS to XYZ CS
    t = np.empty(point_num)
    x = np.empty(point_num)
    y = np.empty(point_num)
    z = np.empty(point_num)
    for i in range(point_num):
        t[i] = timestamp[i]
        (x[i], y[i], z[i]) = geoid.t_latlon_to_xyz(lat[i], lon[i], h[i])
    # interpolate using CubicSpline
    # fit
    cs_x = CubicSpline(t, x)
    cs_y = CubicSpline(t, y)
    cs_z = CubicSpline(t, z)
    # new x axis
    point_num = (point_num - 1) * points_per_gap + point_num
    t = np.linspace(t[0], t[-1], point_num)
    # new data
    x = cs_x(t)
    y = cs_y(t)
    z = cs_z(t)
    # XYZ to lat lon amsl elevation
    new_t = [None] * point_num
    new_lat = [0] * point_num
    new_lon = [0] * point_num
    new_h = [0] * point_num
    for i in range(point_num):
        new_t[i] = datetime.fromtimestamp(t[i], tz = common.local_timezone)
        (new_lat[i], new_lon[i], new_h[i]) = geoid.t_xyz_to_latlonelev(x[i], y[i], z[i])
    
    return (new_t, new_lat, new_lon, new_h, point_num)

def export_kml(
    kml_file_path: str, telemetries: list,
    interpolate_track_points: bool = False,
    interpolate_points_per_gap: int = 3
):
    """
    Export GPS data as KML file. KML version is '2.2'.

    Parameters
    ----------
    telemetries: list
        Result got from garse_video.parse_videos()
    interpolate_track_points: bool
        Use cubic spline to interpolate GPS track points.
    interpolate_points_per_gap: int
        Number of extra inserted points between two previous track points.

    Returns
    ----------
    Nothing
    """

    try:
        import simplekml
    except ImportError:
        common.error('Module simplekml is needed for KML file export.')
    
    interpolate_track_points = True
    interpolate_points_per_gap = 3 # 1/4 second
    
    kml = simplekml.Kml(name = 'Dashcam GPS track')

    track_no = 1
    for telemetry in telemetries:
        telemetry = telemetry['telemetry']
        gps_info = telemetry['gps_info']
        gps_data_num = gps_info['gps_data_num']
        timestamp = [None] * gps_data_num
        lat = [0] * gps_data_num
        lon = [0] * gps_data_num
        height = [0] * gps_data_num
        for i in range(gps_data_num):
            point = gps_info['gps_track'][i]
            if interpolate_track_points:
                timestamp[i] = point['time']
                lat[i] = point['lat'] / 360000
                lon[i] = point['lon'] / 360000
                height[i] = point['height'] / 100
            else:
                (
                    timestamp[i],
                    lat[i], lon[i],
                    h, height[i], geoid_h,
                    speed, heading
                ) = __get_point_info(point)
        # interpolate GPS track points if needed
        if interpolate_track_points:
            (
                timestamp, lat, lon, height, gps_data_num
            ) = __interpolate_track(
                timestamp, lat, lon, height, interpolate_points_per_gap
            )
        # generate kml output
        when = [''] * gps_data_num
        coord = [()] * gps_data_num
        for i in range(gps_data_num):
            when[i] = common.print_iso_timestr(timestamp[i])
            coord[i] = (lon[i], lat[i], height[i])
        # KML
        folder = kml.newfolder(name = 'Track %d' % track_no)
        track = folder.newgxtrack(name = '')
        track.altitudemode = simplekml.AltitudeMode.absolute
        track.newwhen(when)
        track.newgxcoord(coord)
        # KML styling
        track.stylemap.normalstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
        track.stylemap.normalstyle.linestyle.color = '99ffac59'
        track.stylemap.normalstyle.linestyle.width = 6
        track.stylemap.highlightstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
        track.stylemap.highlightstyle.iconstyle.scale = 1.2
        track.stylemap.highlightstyle.linestyle.color = '99ffac59'
        track.stylemap.highlightstyle.linestyle.width = 8

        track_no = track_no + 1

    kml.save(kml_file_path)
