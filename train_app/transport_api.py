#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 22:51
# @Author  : liyun
# @desc    :
from datetime import datetime
from typing import List

from db import NAT
import pytz
from sqlalchemy.orm import Session
from settings import settings
from asyncio import gather
import pandas as pd
import httpx
from helpers import time_to_seconds, tptdt_2_timestamp
from models import Interval
import json
import os


async def download_timetable(station: str, date_str: str, time_str: str, file_path: str, client) -> str:
    """
    Download timetable data using Transport API, and save the data in a json file
    :param station: station code
    :param date_str: date in string format e.g. '2022-02-09'
    :param time_str: time in string format e.g. '14:17'
    :param file_path: path of the json file to be saved
    :param client: httpx client
    :return: the path of the file written
    """
    params = {'app_id': settings.tpt_app_id, 'app_key': settings.tpt_app_key, 'date': date_str, 'time': time_str}
    res = await client.get(f'{settings.tpt_url}/{station}/timetable.json', params=params)
    with open(file_path, 'w') as f:
        json.dump(res.json, f)
    return file_path


async def download_multiple_timetables(station: str, t0: int, dir_name: str) -> List[str]:
    """
    Download multiple timetables. The number to download is determined by the concurrency settings
    :param station: station code
    :param t0: start timestamp
    :param dir_name: the path of the folder for storing the downloaded data
    :return: a list of files downloaded
    """
    download_tasks = []
    async with httpx.AsyncClient() as client:
        for i in range(settings.download_concurrency):
            file_path = os.path.join(dir_name, f'ttp{i}.json')
            dt = datetime.fromtimestamp(t0 + i * settings.t_window, pytz.timezone(settings.tz))
            download_tasks.append(download_timetable(station, dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M'), file_path, client))
        files = await gather(*download_tasks)
    return files



