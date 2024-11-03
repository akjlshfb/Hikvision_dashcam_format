# Common consts and functions

import pytz
from datetime import datetime, timezone

# A recent time for timezone history database
__dt = datetime(2024, 1, 1, 0, 0, 0)

# Use computer's timezone by default
local_timezone = datetime.now().astimezone().tzinfo

# Assume dashcam is at the same timezone as the computer
def adjust_tz(timestamp):
    utc_offset = int(local_timezone.utcoffset(__dt, is_dst = False).total_seconds())
    return timestamp - utc_offset

# Set global timezone for dashcam internal timestamp conversion
def set_timezone(timezone_str: str = None):
    global local_timezone
    if timezone_str != None:
        local_timezone = pytz.timezone(timezone_str)
    else:
        local_timezone = datetime.now().astimezone().tzinfo

def print_iso_timestr(when: datetime) -> str:
    return when.isoformat()

def error(error_msg):
    print('Error: ' + error_msg)
    raise

def warning(warn_msg):
    print('Warning: ' + warn_msg)
    raise
