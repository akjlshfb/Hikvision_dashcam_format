# Parse indexXX.bin, generate result as json

import json
import os

import common

# sd_dir_path = './misc'
# dump_json_to_file = True
# json_file_path = './misc/record_file_index.json'

def parse(sd_dir_path: str, dump_json_to_file: bool = False, json_file_path: str = None) -> dict:
    """
    Parse index00.bin or index01.bin file and get segment infos of mp4 files.

    Parameters
    ----------
    sd_dir_path: str
        SD card path or a folder containing index bin file.
    dump_json_to_file: bool
        When is True, the result dict will be dumped to json_file_path.
    json_file_path: str
        Required when dump_json_to_file is True.

    Returns
    ----------
    record_file_index: dict
        A dictionary containing segment infos.
    """

    index_00_file_name = 'index00.bin'
    index_01_file_name = 'index01.bin'

    # Test file path
    if not os.path.isdir(sd_dir_path):
        common.error('SD card folder doesn''t exist.')
    index_file_path = os.path.join(sd_dir_path, index_00_file_name)
    if (not os.path.isfile(index_file_path)):
        index_file_path = os.path.join(sd_dir_path, index_01_file_name)
        if (not os.path.isfile(index_file_path)):
            common.error('index00.bin or index01.bin not found in SD card folder.')

    record_file_index = {}

    with open(index_file_path, 'rb') as index_file:

        # Seg 1 Overall info

        # Seg 1.1 Total file number
        buf = index_file.read(0x30)
        record_file_num = int.from_bytes(buf[0x0C:0x0E], 'little')
        record_file_index['record_file_num'] = record_file_num

        # Seg 1.2 Last file
        buf = index_file.read(0x30)
        last_file_no = int.from_bytes(buf[0:2], 'little')

        # Seg 1.3 Photo record file
        buf = index_file.read(0x30)
        photo_file_no = int.from_bytes(buf[0x00:0x02], 'little')
        photo_seg_num = int.from_bytes(buf[0x02:0x04], 'little') + 1

        #Seg 2 Unknown

        # Seg 3 Each record file info
        record_file_infos = []
        index_file.seek(0x500)
        for i in range(record_file_num):
            record_file_info = {}
            buf = index_file.read(0x20)
            file_no = int.from_bytes(buf[0x00:0x04], 'little')
            if file_no != i:
                common.warning('Seg 3 file no out of order.')
            record_file_info['file_no'] = file_no
            if file_no != photo_file_no:
                record_file_info['file_type'] = 'video'
                record_file_info['video_write_complete'] = int.from_bytes(buf[0x04:0x06], 'little')
                record_file_info['seg_num'] = int.from_bytes(buf[0x06:0x08], 'little') + 1
                video_type = int.from_bytes(buf[0x10:0x12], 'little')
                if video_type == 2:
                    if file_no != last_file_no:
                        common.error('Seg 3 0x10 - 0x12 error. Normal video should be 0x00 and 0x01.')
                    else:
                        video_type = 0
                record_file_info['is_emergency_file'] = video_type
            else:
                record_file_info['file_type'] = 'photo'
                photo_type = int.from_bytes(buf[0x10:0x12], 'little')
                if photo_type != 2:
                    common.error('Seg 3 0x10 - 0x12 error. Photo should be 0x02.')
                record_file_info['seg_num'] = photo_seg_num

            record_file_infos.append(record_file_info)
        
        # Seg 4 Each segment detailed info
        for file_no in range(record_file_num):
            seg_infos = []
            buf = index_file.read(0x5000)
            for seg_no in range(record_file_infos[file_no]['seg_num']):
                buf2 = buf[seg_no * 0x50 : (seg_no + 1) * 0x50]
                seg_info = {}
                seg_info['seg_no'] = seg_no
                seg_type = buf2[0]
                if file_no != photo_file_no:
                    if seg_type != 0:
                        common.error('Seg 4 0x00 error. Video should be 0x00.')
                    else:
                        seg_info['seg_type'] = 'video'
                else:
                    if seg_type != 2:
                        common.error('Seg 4 0x00 error. Photo should be 0x02.')
                    else:
                        seg_info['seg_type'] = 'photo'
                seg_info['start_time'] = common.adjust_tz(int.from_bytes(buf2[0x08:0x0C], 'little'))
                seg_info['end_time'] = common.adjust_tz(int.from_bytes(buf2[0x10:0x14], 'little'))
                seg_info['start_pos'] = int.from_bytes(buf2[0x28:0x2C], 'little') - 0x40000
                seg_info['end_pos'] = int.from_bytes(buf2[0x2C:0x30], 'little')
                if file_no != photo_file_no:
                    video_type = int.from_bytes(buf2[0x04:0x08], 'little')
                    if video_type == 0x13:
                        seg_info['video_type'] = 'normal'
                    elif video_type == 0x00:
                        seg_info['video_type'] = 'parking'
                    else:
                        common.error('Seg 4 0x04 - 0x08 error. Video should be either of 0x00 and 0x13.')
                    seg_info['video_fps'] = buf2[0x31]
                seg_infos.append(seg_info)
            record_file_infos[file_no]['seg_infos'] = seg_infos
        
        # Done.
        record_file_index['record_file_infos'] = record_file_infos

    if dump_json_to_file:
        if json_file_path != None:
            with open(json_file_path, 'w+') as json_file:
                json.dump(record_file_index, json_file, indent = 2)
        else:
            common.error('Output json file path is missing.')
    
    return record_file_index

def search(record_file_index: dict, start_time: int = -1, end_time: int = -1) -> list:
    """
    Search the index to find video segments in a period.

    Parameters
    ----------
    record_file_index: dict
        Index returned by parse()
    start_time: int
        Timestamp. Default -1: search from the beginning.
    end_time: int
        Timestamp. Default -1: search to the end.

    Returns
    ----------
    result: list
        A list containing all consecutive videos.
    """

    if end_time == -1:
        end_time = (1 << 32)

    temp_result = []

    # Find all video segments that overlap with search period
    for file_info in record_file_index['record_file_infos']:
        if file_info['file_type'] == 'video':
            for seg_info in file_info['seg_infos']:
                if ( # search peroid and segment have overlap
                    ((seg_info['start_time'] <= start_time) and (seg_info['end_time'] >= start_time)) or
                    ((seg_info['start_time'] <= end_time) and (seg_info['end_time'] >= end_time)) or
                    ((seg_info['start_time'] >= start_time) and (seg_info['end_time'] <= end_time))
                ):
                    temp = {}
                    temp['file_no'] = file_info['file_no']
                    temp['seg_no'] = seg_info['seg_no']
                    temp['start'] = seg_info['start_time']
                    temp['end'] = seg_info['end_time']
                    temp['parking'] = (seg_info['video_type'] == 'parking')
                    temp_result.append(temp)

    # Sort to find all consecutive video segments.
    temp_result.sort(key = lambda x: x['start'])

    start_offset = 0
    end_offset = 0
    if len(temp_result) > 0:
        if temp_result[0]['start'] < start_time:
            start_offset = start_time - temp_result[0]['start']
        if temp_result[-1]['end'] > end_time:
            end_offset = temp_result[-1]['end'] - end_time

    last_end = -1
    last_parking = None
    search_result = []

    for seg_info in temp_result:
        if (
            (seg_info['start'] - last_end > 1) or (seg_info['parking'] != last_parking)
        ):
            video_segments = []
            search_result.append(video_segments)
        start = seg_info['start']
        last_end = seg_info['end']
        last_parking = seg_info['parking']
        seg_info['start'] = seg_info['start'] - start
        seg_info['end'] = seg_info['end'] - start
        video_segments.append(seg_info)
    
    if len(temp_result) > 0:
        search_result[0][0]['start'] = start_offset
        search_result[-1][-1]['end'] = search_result[-1][-1]['end'] - end_offset

    return search_result
