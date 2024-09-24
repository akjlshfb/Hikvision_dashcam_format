import gpxpy.gpx
import json
from datetime import datetime

import common
import geoid

gpx_path = './misc/test.gpx'

with open('./misc/temp.json', 'r') as json_file:
    seg_info = json.load(json_file)
gps_info = seg_info['gps_info']
gps_data_num = gps_info['gps_data_num']
gps_track_0 = gps_info['gps_track']
gps_tracks = [gps_track_0]

common.set_timezone('US/Pacific')

# Whether to use a single uniformed geoid height to calc elev
use_uniform_geoid_height = False

# Timeout for consecutive gps_tracks to be considered as seperate tracks.
new_track_timeout = 300 #seconds

#===========================================

def track_desc(gpx_segment) -> str:
    s = gpx_segment.points[0].time.strftime('%Y-%m-%d %H:%M:%S UTC%z')
    e = gpx_segment.points[-1].time.strftime('%Y-%m-%d %H:%M:%S UTC%z')
    l = gpx_segment.length_3d()
    return 'Track info\nStart: %s\nEnd: %s\nToltal length: %.3f km' % (s, e, l / 1000)


if use_uniform_geoid_height:
    # Use first point in first track segment to determine geoid height
    geoid.set_geoid_height(
        gps_tracks[0][0]['lat'] / 360000,
        gps_tracks[0][0]['lon'] / 360000
    )

gpx = gpxpy.gpx.GPX()

last_track_end_time = -1
track_no = 1

gpx_points = []
for gps_track in gps_tracks:
    if (
        not ((last_track_end_time != -1) and 
        (gps_track[0]['time'] - last_track_end_time < 300 * new_track_timeout))
    ):
        gpx_track = gpxpy.gpx.GPXTrack(name = f'Dashcam track {track_no}' )
        gpx.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        if last_track_end_time != -1:
            gpx_track.description = track_desc(gpx_segment)
        track_no = track_no + 1
    for point in gps_track:
        if point['valid'] == 1:
            gpx_point = gpxpy.gpx.GPXTrackPoint()
            gpx_point.time = datetime.fromtimestamp(point['time'], tz = common.timezone)
            gpx_point.latitude = point['lat'] / 360000 # centi sec to deg
            gpx_point.longitude = point['lon'] / 360000 # centi sec to deg
            if use_uniform_geoid_height: # height: cm ellisoidal to m amsl
                gpx_point.elevation = point['height'] / 100 - geoid.geoid_height
                gpx_point.geoid_height = geoid.geoid_height
            else:
                gpx_point.elevation = geoid.get_elev(
                    gpx_point.latitude, gpx_point.longitude, point['height'] / 100
                )
                gpx_point.geoid_height = point['height'] / 100 - gpx_point.elevation
            gpx_point.speed = point['speed'] / 3.6 # km/h to m/s
            gpx_point.course = point['heading']
            gpx_points.append(gpx_point)
    gpx_segment.points = gpx_points
gpx_track.description = track_desc(gpx_segment) # last one

with open(gpx_path, 'w+') as f:
    f.write(gpx.to_xml(version = '1.0'))
