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

def __mov_avg_filter(x, window: int):

    try:
        import numpy as np
    except ImportError:
        common.error('Module simplekml is needed for KML file export.')
    x_len = len(x)
    result = np.zeros(x_len)

    # windows has to be an odd number
    if window % 2 == 0:
        window = window + 1
    # first special ((window + 1) / 2) elements
    special_num = int((window + 1) / 2)
    tmp_sum = x[0]
    result[0] = tmp_sum
    for i in range(1, special_num):
        tmp_sum = tmp_sum + x[i * 2 - 1]
        tmp_sum = tmp_sum + x[i * 2]
        result[i] = tmp_sum / (i * 2 + 1)
    # middle
    for i in range(special_num, x_len - special_num + 1):
        tmp_sum = tmp_sum - x[i - special_num]
        tmp_sum = tmp_sum + x[i + special_num - 1]
        result[i] = tmp_sum / window
    # last special ((window + 1) / 2 + 1) elements
    for i in range(x_len - special_num + 1, x_len):
        j = x_len - i
        tmp_sum = tmp_sum - x[x_len - j * 2]
        tmp_sum = tmp_sum - x[x_len - j * 2 - 1]
        result[i] = tmp_sum / (j * 2 - 1)
    
    return result

def export_kml(
    kml_file_path: str, telemetries: list,
    export_tour: bool = True,
    interpolate_track_points: bool = False,
    interpolate_points_per_gap: int = 3,
    export_elevation: bool = True
):
    """
    Export GPS data as KML file. KML version is '2.2'.

    Parameters
    ----------
    telemetries: list
        Result got from garse_video.parse_videos()
    export_tour: bool
        Whether to include a tour in the generated KML file.
        For the tour parameters, see the consets in the function
    interpolate_track_points: bool
        Use cubic spline to interpolate GPS track points.
    interpolate_points_per_gap: int
        Number of extra inserted points between two previous track points.
    export_elevation: bool
        Include elevation in track coordinates.

    Returns
    ----------
    Nothing
    """

    try:
        import simplekml
        import numpy as np
        from scipy.interpolate import CubicSpline
    except ImportError:
        common.error('Module simplekml is needed for KML file export.')
    
    # Consts for tour
    tour_filter_window_sec = 10 # seconds
    tour_tilt_max = 70 # degrees
    tour_tilt_min = 40 # degrees
    tour_tilt_max_speed = 30 # m/s
    tour_tilt_coeff = (tour_tilt_max - tour_tilt_min) / tour_tilt_max_speed
    tour_range_max = 400 # m
    tour_range_min = 200 # m
    tour_range_max_speed = 30 # m/s
    tour_range_coeff = (tour_range_max - tour_range_min) / tour_range_max_speed
    tour_lookat_late_sec = 3
    tour_heading_calc_threshold = 2.0 # meters. Stop calculating new heading if distance is less than this value.
    tour_heading_filter_window_sec = 7 # seconds. otherwise too dizzy x_x
    tour_kml_refresh_period = 1 # seconds, should be less than points_per_sec
    tour_track_from_start = True # Show track from start, instead of just a small tail
    
    # interpolate_track_points = True
    # interpolate_points_per_gap = 3 # 1/4 second
    if not interpolate_track_points:
        interpolate_points_per_gap = 0
    points_per_sec = interpolate_points_per_gap + 1
    if tour_kml_refresh_period < 1 / points_per_sec:
        print('Warning: tour_kml_refresh_period < 1 / points_per_sec, adjusting...')
        tour_kml_refresh_period = 1 / points_per_sec
    tour_kml_refresh_points = int(points_per_sec * tour_kml_refresh_period)
    
    kml = simplekml.Kml(name = 'Dashcam GPS track')

    track_no = 1
    for telemetry in telemetries:
        telemetry = telemetry['telemetry']
        gps_info = telemetry['gps_info']
        gps_data_num = gps_info['gps_data_num']
        timestamp = [None] * gps_data_num
        time_obj = [None] * gps_data_num
        lat = [0] * gps_data_num
        lon = [0] * gps_data_num
        height = [0] * gps_data_num
        for i in range(gps_data_num):
            point = gps_info['gps_track'][i]
            if export_tour or interpolate_track_points:
                timestamp[i] = point['time']
                lat[i] = point['lat'] / 360000
                lon[i] = point['lon'] / 360000
                height[i] = point['height'] / 100
            else:
                (
                    time_obj[i],
                    lat[i], lon[i],
                    h, height[i], geoid_h,
                    speed, heading
                ) = __get_point_info(point)
        # interpolate GPS track points if needed
        if export_tour or interpolate_track_points:
            point_num = len(timestamp)
            # lat lon CS to XYZ CS
            t = np.empty(point_num)
            x = np.empty(point_num)
            y = np.empty(point_num)
            z = np.empty(point_num)
            for i in range(point_num):
                t[i] = timestamp[i]
            (x, y, z) = geoid.t_latlon_to_xyz(lat, lon, height)
            if interpolate_track_points:
                # interpolate using CubicSpline
                # fit
                cs_x = CubicSpline(t, x)
                cs_y = CubicSpline(t, y)
                cs_z = CubicSpline(t, z)
                # new x axis
                point_num = (point_num - 1) * interpolate_points_per_gap + point_num
                t = np.linspace(t[0], t[-1], point_num)
                # new data
                x = cs_x(t)
                y = cs_y(t)
                z = cs_z(t)
            if export_tour:
                # filter the track to get lootat points
                # use simple moving average filter as LPF
                filter_window_size = tour_filter_window_sec * points_per_sec
                look_x = __mov_avg_filter(x, filter_window_size)
                look_y = __mov_avg_filter(y, filter_window_size)
                look_z = __mov_avg_filter(z, filter_window_size)
                (look_lat, look_lon, look_h) = geoid.t_xyz_to_latlonelev(look_x, look_y, look_z)
                # calculate speed for later use. m/s
                spd_x = np.diff(x) * points_per_sec
                spd_y = np.diff(y) * points_per_sec
                spd_z = np.diff(z) * points_per_sec
                spd_x = np.insert(spd_x, 0, spd_x[0])
                spd_y = np.insert(spd_y, 0, spd_y[0])
                spd_z = np.insert(spd_z, 0, spd_z[0])
                spd = np.sqrt(spd_x ** 2 + spd_y ** 2 + spd_z ** 2)
                # filter speed, otherwize tilt and range would cause dizzy
                look_heading_filter_size = tour_heading_filter_window_sec * points_per_sec
                spd = __mov_avg_filter(spd, look_heading_filter_size)
                # lookat tilt
                look_tilt = np.ones(point_num) * tour_tilt_min + spd * tour_tilt_coeff
                look_tilt = np.clip(look_tilt, tour_tilt_min, tour_tilt_max)
                # lookat range
                look_range = np.ones(point_num) * tour_range_min + spd * tour_range_coeff
                look_range = np.clip(look_range, tour_range_min, tour_range_max)
            # XYZ to lat lon amsl elevation
            time_obj = [None] * point_num
            lat = [0] * point_num
            lon = [0] * point_num
            height = [0] * point_num
            for i in range(point_num):
                time_obj[i] = datetime.fromtimestamp(t[i], tz = common.local_timezone)
            (lat, lon, height) = geoid.t_xyz_to_latlonelev(x, y, z)
            gps_data_num = point_num
            if export_tour:
                # generate heading for tour lookat
                # padding several seconds for filtered lookat points
                # then heading is from lookat point to real point
                look_padding_points = tour_lookat_late_sec * points_per_sec
                look_dx = look_x[1] - look_x[0]
                look_dy = look_y[1] - look_y[0]
                look_dz = look_z[1] - look_z[0]
                look_x_pad = np.linspace(look_x[0] - look_dx * look_padding_points, look_x[0] - look_dx, look_padding_points)
                look_y_pad = np.linspace(look_y[0] - look_dy * look_padding_points, look_y[0] - look_dy, look_padding_points)
                look_z_pad = np.linspace(look_z[0] - look_dz * look_padding_points, look_z[0] - look_dz, look_padding_points)
                (look_lat_pad, look_lon_pad, look_h_pad) = geoid.t_xyz_to_latlonelev(look_x_pad, look_y_pad, look_z_pad)
                look_heading_lat = np.concatenate((look_lat_pad, look_lat[:-look_padding_points]))
                look_heading_lon = np.concatenate((look_lon_pad, look_lon[:-look_padding_points]))
                look_heading = geoid.calc_heading(look_heading_lat, look_heading_lon, lat, lon, tour_heading_calc_threshold)
                # filter heading, otherwise too dizzy
                # need to consider angle wrap issue, thus convert to sine and cosine
                look_heading = np.radians(look_heading)
                look_heading_cos = np.cos(look_heading)
                look_heading_sin = np.sin(look_heading)
                look_heading_cos = __mov_avg_filter(look_heading_cos, look_heading_filter_size)
                look_heading_sin = __mov_avg_filter(look_heading_sin, look_heading_filter_size)
                look_heading = np.arctan2(look_heading_sin, look_heading_cos)
                look_heading = np.degrees(look_heading)
                # #TODO: debug
                # look_coord = [()] * gps_data_num
        # generate track kml data
        when = [''] * gps_data_num
        coord = [()] * gps_data_num
        for i in range(gps_data_num):
            when[i] = common.print_iso_timestr(time_obj[i])
            if export_elevation:
                coord[i] = (lon[i], lat[i], height[i])
            else:
                coord[i] = (lon[i], lat[i])
            # #TODO: debug
            # look_coord[i] = (look_heading_lon[i], look_heading_lat[i], look_h[i])

        # KML
        folder = kml.newfolder(name = 'Track %d' % track_no)

        # KML track
        track = folder.newgxtrack(name = '')
        track.altitudemode = simplekml.AltitudeMode.absolute
        if not export_elevation:
            track.altitudemode = simplekml.AltitudeMode.relativetoground
        track.newwhen(when)
        track.newgxcoord(coord)
        # track styling
        track.stylemap.normalstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
        track.stylemap.normalstyle.linestyle.color = '99ffac59'
        track.stylemap.normalstyle.linestyle.width = 6
        track.stylemap.highlightstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
        track.stylemap.highlightstyle.iconstyle.scale = 1.2
        track.stylemap.highlightstyle.linestyle.color = '99ffac59'
        track.stylemap.highlightstyle.linestyle.width = 8

        # KML tour
        tour = folder.newgxtour(name = 'Track %d tour' % track_no)
        playlist = tour.newgxplaylist()
        # start point
        flyto = playlist.newgxflyto()
        flyto.gxduration = 0
        lookat = simplekml.LookAt()
        lookat.latitude = look_lat[0]
        lookat.longitude = look_lon[0]
        lookat.altitude = look_h[0]
        lookat.altitudemode = simplekml.AltitudeMode.absolute
        lookat.heading = look_heading[0]
        lookat.tilt = look_tilt[0]
        lookat.range = look_range[0]
        lookat_timespan = simplekml.GxTimeSpan()
        lookat_timespan.begin = common.print_iso_timestr(time_obj[0])
        lookat_timespan.end = common.print_iso_timestr(time_obj[0])
        lookat.gxtimespan = lookat_timespan
        flyto.lookat = lookat
        # flying tour
        for i in range(0, gps_data_num - 1, tour_kml_refresh_points):
            next_i = i + tour_kml_refresh_points
            next_i = gps_data_num - 1 if next_i >= gps_data_num else next_i
            flyto = playlist.newgxflyto()
            flyto.gxduration = (next_i - i) / points_per_sec
            flyto.gxflytomode = simplekml.GxFlyToMode.smooth
            lookat = simplekml.LookAt()
            lookat.latitude = look_lat[i]
            lookat.longitude = look_lon[i]
            lookat.altitude = look_h[i]
            lookat.altitudemode = simplekml.AltitudeMode.absolute
            lookat.heading = look_heading[i]
            lookat.tilt = look_tilt[i]
            lookat.range = look_range[i]
            lookat_timespan = simplekml.GxTimeSpan()
            if tour_track_from_start:
                lookat_timespan.begin = common.print_iso_timestr(time_obj[0])
            else:
                lookat_timespan.begin = common.print_iso_timestr(time_obj[i])
            lookat_timespan.end = common.print_iso_timestr(time_obj[next_i])
            lookat.gxtimespan = lookat_timespan
            flyto.lookat = lookat

        # #TODO:debug
        # look_track = folder.newgxtrack(name = 'look_track')
        # look_track.altitudemode = simplekml.AltitudeMode.absolute
        # look_track.newwhen(when)
        # look_track.newgxcoord(look_coord)
        # # look_track styling
        # look_track.stylemap.normalstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
        # look_track.stylemap.normalstyle.linestyle.color = '990000ff'
        # look_track.stylemap.normalstyle.linestyle.width = 6
        # look_track.stylemap.highlightstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
        # look_track.stylemap.highlightstyle.iconstyle.scale = 1.2
        # look_track.stylemap.highlightstyle.linestyle.color = '990000ff'
        # look_track.stylemap.highlightstyle.linestyle.width = 8

        track_no = track_no + 1

    kml.save(kml_file_path)
