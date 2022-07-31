#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 22:51
# @Author  : liyun
# @desc    :
from datetime import datetime
from db import NAT
import pytz
from sqlalchemy.orm import Session
from settings import settings
from asyncio import gather
import pandas as pd
import httpx

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


def parse_timetable(json_obj: dict) -> pd.DataFrame or None:
    """
    Parse the json format timetable received from the Transport API
    :param json_obj: a json dictionary object
    :return: the timetable dataframe, or None if the station of interest has no departure information
    """
    date_str, time_str, dept_list = json_obj['date'], json_obj['time_of_day'], json_obj['departures']['all']
    if not len(dept_list):
        return None
    d_ref, t_ref = int(datetime.strptime(date_str, '%Y-%m-%d').timestamp()), time_to_seconds(time_str, 0)
    adt = [d_ref + time_to_seconds(t['aimed_departure_time'], t_ref) if t['aimed_departure_time'] is not None else NAT
           for t in dept_list]
    aat = [d_ref + time_to_seconds(t['aimed_arrival_time'], t_ref) if t['aimed_arrival_time'] is not None else NAT
           for t in dept_list]
    df = pd.DataFrame({'aimed_departure_timestamp': adt, 'aimed_arrival_timestamp': aat})
    df[['service', 'train_uid']] = [int(s['service']) for s in dept_list], [t['train_uid'] for t in dept_list]
    df['station_code'] = json_obj['station_code']
    return df


async def download_timetable(station: str, date_str: str, time_str: str, client) -> pd.DataFrame:
    """
    Download timetable data using Transport API
    :param station: station code
    :param date_str: date in string format e.g. '2022-02-09'
    :param time_str: time in string format e.g. '14:17'
    :param client: httpx client
    :return: a pandas dataframe containing the data
    """
    params = {'app_id': settings.tpt_app_id, 'app_key': settings.tpt_app_key, 'date': date_str, 'time': time_str}
    res = await client.get(f'{settings.tpt_url}/{station}/timetable.json', params=params)
    return parse_timetable(res.json())


async def download_multiple_timetables(station: str, t0: int) -> pd.DataFrame:
    """
    Download multiple timetables. The number to download is determined by the concurrency settings
    :param station: station code
    :param t0: start timestamp
    :return: a timetable dataframe produced by combining the individual timetables
    """
    download_tasks = []
    async with httpx.AsyncClient() as client:
        for i in range(settings.download_concurrency):
            dt = datetime.fromtimestamp(t0 + i * settings.t_window, pytz.timezone(settings.tz))
            download_tasks.append(download_timetable(station, dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M'), client))
        timetables = await gather(*download_tasks)
    return pd.DataFrame([df for df in timetables if df is not None])


async def load_timetable(station: str, t0: int, db: Session):
    """
    Download timetables and store them into database
    :param station: station code
    :param t0: start timestamp of the timetable
    :param db: db session
    :return:
    """
