# main script to process data

import os
from datetime import datetime, timezone

import common
import parse_index
import parse_video
import export_gps

#debug
import json

# ===== init =====

# Use pytz.all_timezones to see all timezones
timezone_str = 'US/Pacific'

# Set global timezone
common.set_timezone(timezone_str)

sd_dir_path = './misc'
# sd_dir_path = 'D:/'
index_json_path = './misc/record_file_index.json'

# # ===== parse index =====

# record_file_index = parse_index.parse(sd_dir_path, True, index_json_path)

# # ===== search segment =====

# # start = int(datetime(2024, 3, 9, 18, 5, 20, 0).timestamp())
# # end = int(datetime(2024, 3, 9, 18, 6, 40, 0).timestamp())
# # start = int(datetime(2024, 6, 30, 1, 20, 15, 0).timestamp())
# # end = int(datetime(2024, 6, 30, 1, 30, 15, 0).timestamp())
# start = int(datetime(2024, 9, 21, 15, 48, 20, 0).timestamp())
# end = int(datetime(2024, 9, 21, 16, 17, 00, 0).timestamp())

# search_result = parse_index.search(record_file_index, start, end)

# with open('./misc/search.json', 'w+') as f:
#     json.dump(search_result, f, indent = 2)

# ===== parse video =====

# ## parse seg test

# parse_options = {
#     'export_video': True,
#     'export_video_path': './misc/test.mp4',
#     'export_thumbnail': True,
#     'export_thumbnail_path': './misc/thumb.jpg',
#     'gps_track': True,
#     'acce': True,
#     'image_label': False
# }

# file_no = 135
# seg_no = 0
# start_sec = search_result[0][0]['start']
# end_sec = search_result[0][0]['end']

# parse_seg_result = parse_video.parse_seg(
#     sd_dir_path, file_no, seg_no, record_file_index,
#     parse_options, start_sec, end_sec
# )

# with open('./misc/temp.json', 'w+') as json_file:
#     json.dump(parse_seg_result, json_file, indent = 2)

# ## parse video test

# parse_options = {
#     "export_video": True,
#     "export_video_path": "./misc/test.mp4",
#     "gps_track": True,
#     "acce": True,
#     "image_label": False
# }

# parse_video_result = parse_video.parse_video(
#     sd_dir_path, search_result[0], record_file_index, parse_options
# )

# with open('./misc/temp.json', 'w+') as json_file:
#     json.dump(parse_video_result, json_file, indent = 2)

# ## parse videos test

# parse_options = {
#     "export_videos": False,
#     "export_videos_folder": "./misc/",
#     "gps_track": True,
#     "acce": True,
#     "image_label": False
# }

# parse_videos_result = parse_video.parse_videos(
#     sd_dir_path, search_result, record_file_index, parse_options
# )

# with open('./misc/temp.json', 'w+') as json_file:
#     json.dump(parse_videos_result, json_file, indent = 2)


# ===== debug load json =====

## parse videos test
with open('./misc/temp.json', 'r') as json_file:
    parse_videos_result = json.load(json_file)
with open(index_json_path, 'r') as json_file:
    record_file_index = json.load(json_file)

# # ===== export geojson =====

# gpx_file_path = './misc/test.geojson'

# export_gps.export_geojson(gpx_file_path, parse_videos_result, True)

# # ===== export gpx =====

# gpx_file_path = './misc/test.gpx'

# export_gps.export_gpx(gpx_file_path, parse_videos_result)

# ===== export kml =====

kml_file_path = './misc/test_export.kml'

export_gps.export_kml(
    kml_file_path, parse_videos_result,
    export_tour = True,
    interpolate_track_points = True
)
