#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/31 8:42
# @Author  : liyun
# @desc    :
from datetime import datetime
from settings import settings
import pytz

tz = pytz.timezone(settings.tz)
SECONDS_IN_A_DAY = 86400


def time_to_seconds(time_str: str, t_ref: int) -> int:
    """
    Convert the time in hh:mm format into seconds of the day.
    :param time_str: e.g. 14:20.
    :param t_ref: reference time for cross-day conversion
    :return: the seconds of the time since midnight
    """
    seconds = int(time_str[:2]) * 3600 + int(time_str[-2:]) * 60
    return seconds if seconds >= t_ref else SECONDS_IN_A_DAY + seconds  # todo: consider t_str=00:00


def tptdt_2_timestamp(dt: str) -> int:
    """
    Convert a Transport API style datetime string into timestamp (total seconds since 1970-01-01 UTC)
    :param dt: a Transport API style datetime string e.g. '2022-02-19 14:19'
    :return: timestamp
    """
    return int(datetime.strptime(dt, '%Y-%m-%d %H:%M').replace(tzinfo=tz).timestamp())