# Parse video segment, generate playable video, GPS track, etc.

import os
import struct
import copy
import time
from datetime import datetime, timezone

import common

#===========================================

def parse_seg(
        file_no: int, seg_no: int,
        sd_dir_path: str,
        record_file_index: dict,
        parse_options: dict,
        start_sec: int = -1, end_sec: int = -1,
        video_file_adding = False
    ) -> dict:
    """
    Parse a segment to get video, GPS track, etc.

    Parameters
    ----------
    record_file_index: dict
        Index returned by parse_index.parse()
    parse_options: dict
        See readme.md
    start_sec: int
        When to start parsing. First is 0. -1 means first.
    end_sec: int
        When to stop parsing. Last is (len-1). -1 means last.

    Returns
    ----------
    result: dict
        A dict containing various info.
    """

    seg_info = record_file_index['record_file_infos'][file_no]['seg_infos'][seg_no]
    parse_seg_result = {}

    video_file_name = 'hiv%05d.mp4' % file_no
    video_file_path = os.path.join(sd_dir_path, video_file_name)
    with open(video_file_path, 'rb') as f:

        # Seg 1 Video timestamp and GPS
        f.seek(seg_info['start_pos'])
        # header
        buf = f.read(0x20)
        seg_len_sec = int(int.from_bytes(buf[0x1C:0x1E], 'little') / 0x30)
        if start_sec < 0:
            start_sec = 0
        parse_to_end = False
        if end_sec == -1 or end_sec >= seg_len_sec - 1:
            end_sec = seg_len_sec - 1
            parse_to_end = True
        seg_len_sec = end_sec + 1 - start_sec
        sec_offsets = [0] * seg_len_sec
        gps_info = {}
        if parse_options['gps_track']:
            if seg_info['video_type'] == 'parking':
                gps_info['gps_data_num'] = 1
                gps_track = []
            else:
                gps_info['gps_data_num'] = seg_len_sec
                point = {}
                point['time'] = 0
                point['valid'] = 0
                point['lat'] = 0
                point['lon'] = 0
                point['height'] = 0
                point['speed'] = 0
                point['heading'] = 0
                gps_track = [copy.deepcopy(point) for x in range(seg_len_sec)]
            gps_info['gps_track'] = gps_track
        else:
            gps_info['gps_data_num'] = 0
            gps_info['gps_track'] = []
        parse_seg_result['gps_info'] = gps_info
        # body
        f.seek(f.tell() + 0x30 * start_sec)
        for i in range(seg_len_sec):
            buf = f.read(0x30)
            # File offset for each second
            sec_offsets[i] = int.from_bytes(buf[0x08:0x0C], 'little')
            # GPS
            if parse_options['gps_track'] and seg_info['video_type'] == 'parking' and i == start_sec:
                # in parking mode, all GPS data are same, only read one
                point = {}
                point['time'] = common.adjust_tz(int.from_bytes(buf[0x04:0x08], 'little'))
                point['valid'] = buf[0x24]
                point['lat'] = int.from_bytes(buf[0x14:0x18], 'little')
                point['lon'] = int.from_bytes(buf[0x10:0x14], 'little')
                point['height'] = int.from_bytes(buf[0x20:0x24], 'little')
                point['speed'] = int.from_bytes(buf[0x18:0x1C], 'little')
                point['heading'] = int(int.from_bytes(buf[0x1C:0x20], 'little') / 100)
                if buf[0x25] == ord('W'):
                    point['lon'] = -point['lon']
                if buf[0x26] == ord('S'):
                    point['lat'] = -point['lat']
                gps_track.append(point)
            if parse_options['gps_track'] and seg_info['video_type'] != 'parking':
                # in seg 1, only height is accurate
                gps_track[i]['height'] = int.from_bytes(buf[0x20:0x24], 'little')
        if not parse_to_end:
            buf = f.read(0x30)
            sec_offsets.append(int.from_bytes(buf[0x08:0x0C], 'little'))

        # Seg 2 Emergency
        f.seek(seg_info['start_pos'] + 0x10000)
        # header
        buf = f.read(0x20)
        emergency_video_num = int(int.from_bytes(buf[0x1C:0x1E], 'little') / 0x10)
        emergency_info = {}
        emergency_video_timestamps = [0] * emergency_video_num
        emergency_info['emergency_video_num'] = emergency_video_num
        emergency_info['emergency_video_timestamps'] = emergency_video_timestamps
        # body
        for i in range(emergency_video_num):
            buf = f.read(0x10)
            emergency_video_timestamps[i] = common.adjust_tz(int.from_bytes(buf[0x04:0x08], 'little'))
        parse_seg_result['emergency_info'] = emergency_info

        # Seg 3 Thumbnail
        if parse_options['export_thumbnail']:
            f.seek(seg_info['start_pos'] + 0x20000)
            # header
            buf = f.read(0x20)
            export_thumbnail_len = int.from_bytes(buf[0x1C:0x1E], 'little')
            buf = f.read(export_thumbnail_len)
            of = open(parse_options['export_thumbnail_path'], 'wb+')
            of.write(buf)
            of.close()
        
        # Seg 5 Video and telemetry
        seg_start_pos = seg_info['start_pos'] + 0x40000 + sec_offsets[0]
        if parse_to_end:
            seg_end_pos = seg_info['end_pos']
        else:
            seg_end_pos = seg_info['start_pos'] + 0x40000 + sec_offsets[-1]
        
        f.seek(seg_start_pos)
        if parse_options['export_video']:
            if video_file_adding:
                of = open(parse_options['export_video_path'], 'ab+')
            else:
                of = open(parse_options['export_video_path'], 'wb+')
        acce_num = 0
        acce_log = []
        gps_num = 0
        
        # Read SCRB from the first PS header
        buf = f.read(4)
        buf = f.read(5)
        scrb = (buf[0] % (1 << 5)) >> 3
        scrb = (scrb << 2) + (buf[0] % (1 << 2))
        scrb = (scrb << 8) + buf[1]
        scrb = (scrb << 5) + (buf[2] >> 3)
        scrb = (scrb << 2) + (buf[2] % (1 << 2))
        scrb = (scrb << 8) + buf[3]
        scrb = (scrb << 5) + (buf[4] >> 3)
        seg_pts_start = scrb
        f.seek(seg_start_pos)

        # Parse Program Stream
        while(f.tell() < seg_end_pos):
            stream_head = f.read(6)
            if stream_head[3] == 0xBA:
                # PS header
                if parse_options['export_video']:
                    buf = f.read(14)
                    of.write(stream_head)
                    of.write(buf)
                else:
                    f.seek(f.tell() + 14)
            else:
                # PES packet
                pes_len = int.from_bytes(stream_head[4:6], 'big')
                if stream_head[3] != 0xBD:
                    # not private_stream_1
                    if parse_options['export_video']:
                        buf = f.read(pes_len)
                        of.write(stream_head)
                        of.write(buf)
                    else:
                        f.seek(f.tell() + pes_len)
                else:
                    # private_stream_1
                    if (
                        (not parse_options['acce']) and 
                        (not parse_options['gps_track']) and 
                        (not parse_options['image_label'])
                    ):
                        f.seek(f.tell() + pes_len)
                        continue
                    # PES_packet header
                    buf = f.read(10)
                    pts = (buf[3] % (1 << 3)) >> 1
                    pts = (pts << 8) + buf[4]
                    pts = (pts << 7) + (buf[5] >> 1)
                    pts = (pts << 8) + buf[6]
                    pts = (pts << 7) + (buf[7] >> 1)
                    # private_header
                    buf = f.read(pes_len - 10)
                    pkt_id = int.from_bytes(buf[0:2], 'big')
                    sub_pkt_id = int.from_bytes(buf[4:6], 'big')
                    # private_data
                    if (
                        (pkt_id == 0x0802) and (sub_pkt_id == 0x0007) and 
                        (parse_options['acce'] or parse_options['gps_track'])
                    ):
                        # binary GPS/acce data
                        data_type = int.from_bytes(buf[0x14:0x16], 'little')
                        year = int.from_bytes(buf[0x24:0x26], 'little')
                        mon = int.from_bytes(buf[0x26:0x28], 'little')
                        day = int.from_bytes(buf[0x2A:0x2C], 'little')
                        hour = int.from_bytes(buf[0x2C:0x2E], 'little')
                        min = int.from_bytes(buf[0x2E:0x30], 'little')
                        sec = int.from_bytes(buf[0x30:0x32], 'little')
                        ms = int((pts / 90 - seg_pts_start / 90) % 1000)
                        dt = datetime(year, mon, day, hour, min, sec, ms * 1000, tzinfo = timezone.utc)
                        time_ms = int(common.adjust_tz(dt.timestamp()) * 1000)
                        if (data_type == 0x10) and parse_options['acce']:
                            acce_data = {}
                            acce_data['time_ms'] = time_ms
                            acce_data['x'] = int.from_bytes(buf[0x70:0x74], 'little', signed = True)
                            acce_data['y'] = int.from_bytes(buf[0x6C:0x70], 'little', signed = True)
                            acce_data['z'] = int.from_bytes(buf[0x68:0x6C], 'little', signed = True)
                            acce_log.append(acce_data)
                            acce_num = acce_num + 1
                        elif (
                            (data_type == 0x20) and parse_options['gps_track'] and 
                            (not (seg_info['video_type'] == 'parking'))
                        ):
                            if (gps_num < seg_len_sec):
                                point = gps_track[gps_num]
                                point['time'] = int(common.adjust_tz(dt.timestamp()))
                                point['valid'] = buf[0x76]
                                lat = int(struct.unpack('<d', buf[0x64:0x6C])[0] * 360000)
                                lon = int(struct.unpack('<d', buf[0x6C:0x74])[0] * 360000)
                                if buf[0x74] == ord('S'):
                                    lat = -lat
                                if buf[0x75] == ord('W'):
                                    lon = -lon
                                point['lat'] = lat
                                point['lon'] = lon
                                point['speed'] = int(struct.unpack('<f', buf[0x78:0x7C])[0])
                                point['heading'] = int(struct.unpack('<f', buf[0x7C:0x80])[0])
                                gps_num = gps_num + 1

        acce_info = {}
        acce_info['acce_num'] = acce_num
        acce_info['acce_log'] = acce_log
        parse_seg_result['acce_info'] = acce_info
        if parse_options['export_video']:
            of.close()
    
    return parse_seg_result

def parse_video(
        video_segs: list,
        sd_dir_path: str,
        record_file_index: dict,
        parse_options: dict
    ) -> dict:
    """
    Parse a segment to get video, GPS track, etc.

    Parameters
    ----------
    video_segs: list
        Contains segments of a consecutive video. From parse_index.search()[]. See readme.md
    record_file_index: dict
        Index returned by parse_index.parse()
    parse_options: dict
        See readme.md

    Returns
    ----------
    result: dict
        A dict containing various info.
    """

    parse_video_result = {}
    gps_info = {}
    gps_data_num = 0
    gps_track = []
    acce_info = {}
    acce_num = 0
    acce_log = []

    parse_seg_options = copy.deepcopy(parse_options)
    parse_seg_options['export_thumbnail'] = False

    if parse_options['export_video']:
        # Create and clear video export file
        f = open(parse_options['export_video_path'], 'wb+')
        f.close()

    for segment in video_segs:
        file_no = segment['file_no']
        seg_no = segment['seg_no']
        start_sec = segment['start']
        end_sec = segment['end']

        parse_seg_result = parse_seg(
            file_no, seg_no, sd_dir_path, record_file_index,
            parse_seg_options, start_sec, end_sec,
            video_file_adding = True # Adding to video export file
        )

        gps_data_num = gps_data_num + parse_seg_result['gps_info']['gps_data_num']
        gps_track = gps_track + parse_seg_result['gps_info']['gps_track']
        acce_num = acce_num + parse_seg_result['acce_info']['acce_num']
        acce_log = acce_log + parse_seg_result['acce_info']['acce_log']
    
    gps_info['gps_data_num'] = gps_data_num
    gps_info['gps_track'] = gps_track
    parse_video_result['gps_info'] = gps_info

    acce_info['acce_num'] = acce_num
    acce_info['acce_log'] = acce_log
    parse_video_result['acce_info'] = acce_info

    return parse_video_result
