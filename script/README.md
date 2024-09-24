# 记录文件处理脚本

## 依赖

tzinfo gpxpy pyproj

## record_file_index

```json
{
    "record_file_num": 234,
    "record_file_infos": [
        {
            "file_no": 12,
            "file_type": "photo",
            "seg_num": 34,
            "seg_infos": [
                {
                    "seg_no": 0,
                    "seg_type": "photo",
                    "start_time": 1701109144,
                    "end_time": 1701118239,
                    "start_pos": 0,
                    "end_pos": 4390912
                },
                ...
            ]
        },
        ...
        {
            "file_no": 56,
            "file_type": "video",
            "video_write_complete": 1,
            "seg_num": 7,
            "is_emergency_file": 1,
            "seg_infos": [
                {
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

## search_result

```json
[
    [
        {
            "file_no": 0,
            "seg_no": 0,
            "start": 0,
            "end": 10,
            "parking": false
        },
        ...
    ],
    ...
]
```

## parse_video.parse_seg parse_options

```json
{
    "export_video": true,
    "export_video_path": "./misc/test.mp4",
    "export_thumbnail": true,
    "export_thumbnail_path": "./misc/thumb.jpg",
    "gps_track": true,
    "acce": true,
    "image_label": false
}
```

## parse_video.parse_video

### video_segs

```json
[
    {
        "file_no": 0,
        "seg_no": 0,
        "start": 0,
        "end": 10,
        "parking": false
    },
    ...
]
```

### parse_options

```json
{
    "export_video": true,
    "export_video_path": "./misc/test.mp4",
    "gps_track": true,
    "acce": true,
    "image_label": false
}
```
