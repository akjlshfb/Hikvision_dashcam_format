# 记录文件处理脚本

## 依赖

tzinfo gpxpy pyproj

## parse_index.parse()

### record_file_index

```json
{
    "record_file_num": 234,
    "record_file_infos": [
        { //photo file
            "file_no": 12,
            "file_type": "photo",
            "seg_num": 34, //photo group numbers in file
            "seg_infos": [
                { //photo group 0
                    "seg_no": 0,
                    "seg_type": "photo",
                    "start_time": 1234567890,
                    "end_time": 1234567899,
                    "start_pos": 0,
                    "end_pos": 4390912
                },
                ...
            ]
        },
        ...
        { //video file
            "file_no": 56,
            "file_type": "video",
            "video_write_complete": 1,
            "seg_num": 7, //video segments in file
            "is_emergency_file": 1,
            "seg_infos": [
                { //video seg 0
                    "seg_no": 0,
                    "seg_type": "video",
                    "start_time": 1234567890,
                    "end_time": 1234567899,
                    "start_pos": 0,
                    "end_pos": 123456,
                    "video_type": "normal",
                    "video_fps": 30
                },
                ...
            ]
        },
        ...
    ]
}
```

## parse_index.search()

### search_result

```json
[ //result videos
    [ //video 0
        { //seg 0 of video 0
            "file_no": 0,
            "seg_no": 0,
            "start": 0, //second to start parse in seg (include)
            "end": 10, //second to stop parse in seg (include)
            "parking": false
        },
        ...
    ],
    ...
]
```

## parse_video.parse_seg

### parse_options

```json
{
    "export_video": true, //if true, export_video_path is required
    "export_video_path": "./test/test.mp4",
    "export_video_adding": false, //to add to file. Optional. False by default
    "export_thumbnail": true, //if true, export_thumbnail_path is required
    "export_thumbnail_path": "./test/thumb.jpg",
    "gps_track": true, //return GPS track
    "acce": true, //return accelerometer data
    "image_label": false //TODO
}
```

### parse_seg_result

```json
{
    "gps_info": {
        //Exist if parse_options['gps_track'] == true
        "gps_data_num": 123,
        "gps_track": [
            {
                "time": 1234567890, //second
                "valid": 1,
                "lat": 14366252, //centisecond
                "lon": 41900859, //centisecond
                "height": 27600, //centimeter
                "speed": 39, //km/h
                "heading": 268 //degree
            },
            ...
        ]
    },
    "acce_info": {
        "acce_num": 4567,
        "acce_log": [
            {
                "time_ms": 1719735615302, //millisecond
                "x": 19, //cm/s^2, left is positive
                "y": -7, //cm/s^2, front is positive
                "z": 981 //cm/s^2, down is positive
            },
            ...
        ]
    }
}
```

## parse_video.parse_video

### video_segs

```json
[ //video
    { //seg 0 of video 0
        "file_no": 0,
        "seg_no": 0,
        "start": 0, //second to start parse in seg (include)
        "end": 10, //second to stop parse in seg (include)
        "parking": false
    },
    ...
]
```

### parse_options

```json
{
    "export_video": true, //if true, export_video_path is required
    "export_video_path": "./test/test.mp4",
    "gps_track": true, //return GPS track
    "acce": true, //return accelerometer data
    "image_label": false //TODO
}
```

### parse_video_result

See [parse_seg_result](#parse_video_result).

Plus a field `"parking": true` to tell if this video is a parking video.

## parse_video.parse_videos

### videos

```json
[ //videos
    [ //video 0
        { //seg 0 of video 0
            "file_no": 0,
            "seg_no": 0,
            "start": 0, //second to start parse in seg (include)
            "end": 10, //second to stop parse in seg (include)
            "parking": false
        },
        ...
    ],
    ...
]
```

### parse_options

```json
{
    "export_videos": true,
    "export_videos_folder": "./test/", //required when export_videos = True
    "export_video_names": [
        //Optional. If exists, the number must match len(videos)
        "test0.mp4", //name for each export video file
        "test1.mp4",
        ...
    ],
    "gps_track": true, //return GPS track
    "acce": true, //return accelerometer data
    "image_label": false //TODO
}
```

### parse_videos_result

```json
[
    { //video 0
        //video_file_name only exists if parse_options['export_videos'] = True
        //If file name is not provided, default name is YYYYMMDDhhmmss.mp4.
        //The time is when video starts. Time zone is from common.timezone.
        "video_path": "./test/20240101081530.mp4",
        "telemetry": parse_video_result //See parse_video_result or parse_seg_result
    },
    ...
]
```

## export_gps.export_gpx

### telemetries

See [parse_vidoes_result](#parse_vidoes_result).
