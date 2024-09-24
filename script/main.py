# main script to process data

import os
from datetime import datetime, timezone

import common
import parse_index
import parse_video

#debug
import json

# ===== init =====

# Use pytz.all_timezones to see all timezones
timezone_str = 'US/Pacific'

# Set global timezone
common.set_timezone(timezone_str)

sd_dir_path = './misc'
index_json_path = './misc/record_file_index.json'

# ===== parse index =====

record_file_index = parse_index.parse(sd_dir_path, True, index_json_path)

# ===== search segment =====

# start = int(datetime(2024, 3, 9, 18, 5, 20, 0).timestamp())
# end = int(datetime(2024, 3, 9, 18, 6, 40, 0).timestamp())
start = int(datetime(2024, 6, 30, 1, 20, 15, 0).timestamp())
end = int(datetime(2024, 6, 30, 1, 30, 15, 0).timestamp())

search_result = parse_index.search(record_file_index, start, end)

with open('./misc/search.json', 'w+') as f:
    json.dump(search_result, f, indent = 2)

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
#     file_no, seg_no,sd_dir_path, record_file_index,
#     parse_options, start_sec, end_sec
# )

# with open('./misc/temp.json', 'w+') as json_file:
#     json.dump(parse_seg_result, json_file, indent = 2)

## parse video test

parse_options = {
    "export_video": True,
    "export_video_path": "./misc/test.mp4",
    "gps_track": True,
    "acce": True,
    "image_label": False
}

parse_video_result = parse_video.parse_video(
    search_result[0], sd_dir_path, record_file_index, parse_options
)

with open('./misc/temp.json', 'w+') as json_file:
    json.dump(parse_video_result, json_file, indent = 2)
