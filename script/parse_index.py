# Parse indexXX.bin, generate result as json

import json
import os
import time

sd_dir_path = './misc'
json_output_dir = sd_dir_path

index_00_file_name = 'index00.bin'
index_01_file_name = 'index01.bin'

json_file_name = 'record_file_index.json'

def print_error(error_msg):
    print('Error: ' + error_msg)
    raise

def print_warning(warn_msg):
    print('Warning: ' + warn_msg)
    raise

# Assume dashcam is at the same timezone as the computer
def adjust_tz(timestamp):
    return timestamp - time.timezone


# Test file path
if not os.path.isdir(sd_dir_path):
    print_error('SD card folder doesn''t exist.')
index_file_path = os.path.join(sd_dir_path, index_00_file_name)
if (not os.path.isfile(index_file_path)):
    index_file_path = os.path.join(sd_dir_path, index_01_file_name)
    if (not os.path.isfile(index_file_path)):
        print_error('index00.bin or index01.bin not found in SD card folder.')

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
            print_warning('Seg 3 file no out of order.')
        record_file_info['file_no'] = file_no
        if file_no != photo_file_no:
            record_file_info['file_type'] = 'video'
            record_file_info['video_write_complete'] = int.from_bytes(buf[0x04:0x06], 'little')
            record_file_info['seg_num'] = int.from_bytes(buf[0x06:0x08], 'little') + 1
            video_type = int.from_bytes(buf[0x10:0x12], 'little')
            if video_type == 2:
                if file_no != last_file_no:
                    print_error('Seg 3 0x10 - 0x12 error. Normal video should be 0x00 and 0x01.')
                else:
                    video_type = 0
            record_file_info['is_emergency_file'] = video_type
        else:
            record_file_info['file_type'] = 'photo'
            photo_type = int.from_bytes(buf[0x10:0x12], 'little')
            if photo_type != 2:
                print_error('Seg 3 0x10 - 0x12 error. Photo should be 0x02.')
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
                    print_error('Seg 4 0x00 error. Video should be 0x00.')
                else:
                    seg_info['seg_type'] = 'video'
            else:
                if seg_type != 2:
                    print_error('Seg 4 0x00 error. Photo should be 0x02.')
                else:
                    seg_info['seg_type'] = 'photo'
            seg_info['start_time'] = adjust_tz(int.from_bytes(buf2[0x08:0x0C], 'little'))
            seg_info['end_time'] = adjust_tz(int.from_bytes(buf2[0x10:0x14], 'little'))
            seg_info['start_pos'] = int.from_bytes(buf2[0x28:0x2C], 'little') - 0x40000
            seg_info['end_pos'] = int.from_bytes(buf2[0x2C:0x30], 'little')
            if file_no != photo_file_no:
                video_type = int.from_bytes(buf2[0x04:0x08], 'little')
                if video_type == 0x13:
                    seg_info['video_type'] = 'normal'
                elif video_type == 0x00:
                    seg_info['video_type'] = 'parking'
                else:
                    print_error('Seg 4 0x04 - 0x08 error. Video should be either of 0x00 and 0x13.')
                seg_info['video_fps'] = buf2[0x31]
            seg_infos.append(seg_info)
        record_file_infos[file_no]['seg_infos'] = seg_infos
    
    # Done.
    record_file_index['record_file_infos'] = record_file_infos

json_file_path = os.path.join(json_output_dir, json_file_name)
with open(json_file_path, 'w+') as json_file:
    json.dump(record_file_index, json_file, indent = 2)
