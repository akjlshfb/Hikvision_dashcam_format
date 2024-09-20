# Common consts and functions

import time

# Assume dashcam is at the same timezone as the computer
def adjust_tz(timestamp):
    return timestamp - time.timezone