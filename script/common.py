# Common consts and functions

import pytz
from datetime import datetime

# A recent time for timezone history database
__dt = datetime(2024, 1, 1, 0, 0, 0)

# Use computer's timezone by default
timezone = datetime.now().astimezone().tzinfo

# Assume dashcam is at the same timezone as the computer
def adjust_tz(timestamp):
    utc_offset = int(timezone.utcoffset(__dt, is_dst = False).total_seconds())
    return timestamp - utc_offset

# Set global timezone for dashcam internal timestamp conversion
def set_timezone(timezone_str: str | None):
    global timezone
    if timezone_str != None:
        timezone = pytz.timezone(timezone_str)
    else:
        timezone = datetime.now().astimezone().tzinfo

def error(error_msg):
    print('Error: ' + error_msg)
    raise

def warning(warn_msg):
    print('Warning: ' + warn_msg)
    raise
