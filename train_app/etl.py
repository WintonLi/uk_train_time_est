#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/31 11:50
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
from helpers import time_to_seconds, tptdt_2_timestamp
from models import Interval
from transport_api import download_multiple_timetables
import tempfile
import json
from repositories import IntervalRepo, TimetableRepo
from schemas import IntervalCreate


def parse_timetable(json_obj: dict) -> pd.DataFrame or None:
    """
    Parse the json format timetable received from the Transport API
    :param json_obj: a json dictionary object
    :return: the timetable dataframe, or None if the station of interest has no departure information
    """
    date_str, time_str, dept_list = json_obj['date'], json_obj['time_of_day'], json_obj['departures']['all']
    if not len(dept_list):
        return None
    d_ref, t_ref = tptdt_2_timestamp(f'{date_str} 00:00'), time_to_seconds(time_str, 0)
    adt = [d_ref + time_to_seconds(t['aimed_departure_time'], t_ref) if t['aimed_departure_time'] is not None else NAT
           for t in dept_list]
    aat = [d_ref + time_to_seconds(t['aimed_arrival_time'], t_ref) if t['aimed_arrival_time'] is not None else NAT
           for t in dept_list]
    df = pd.DataFrame({'aimed_departure_timestamp': adt, 'aimed_arrival_timestamp': aat})
    df[['service', 'train_uid']] = [int(s['service']) for s in dept_list], [t['train_uid'] for t in dept_list]
    return df


def update_timetable(station: str, t0: int, df_ttb: pd.DataFrame, db: Session):
    """
    Update interval and timetable records
    :param station: station code
    :param t0: start timestamp of the timetable
    :param df_ttb: a contiguous timetable dataframe
    :param db: db session
    :return:
    """
    df_adt_valid = df_ttb[df_ttb['aimed_departure_timestamp'] != NAT]
    if not len(df_adt_valid):  # do nothing if no valid departure timestamp
        return
    # remove all records that have neither departure nor arrival time
    df_ttb = df_ttb[(df_ttb['aimed_departure_timestamp'] != NAT) | (df_ttb['aimed_arrival_timestamp'] != NAT)]

    t_max = df_adt_valid['aimed_departure_timestamp'].max()
    interval_left = IntervalRepo.fetch_including(db, station, t0)
    interval_right = IntervalRepo.fetch_including(db, station, t_max)
    intervals_to_merge = list(IntervalRepo.fetch_included(db, station, t0, t_max))
    interval_new = IntervalCreate(**{'station_code': station, 'start_timestamp': t0, 'stop_timestamp': t_max})
    if interval_left is not None:
        interval_new.start_timestamp = interval_left.start_timestamp
        intervals_to_merge.append(interval_left)
    if interval_right is not None:
        interval_new.stop_timestamp = interval_right.stop_timestamp
        intervals_to_merge.append(interval_right)

    # todo: use transactions
    interval = IntervalRepo.create(db, interval_new)
    if not len(intervals_to_merge):  # for a completely new interval
        df_ttb['interval_id'] = interval.id
        TimetableRepo.bulk_insert_by_df(db, df_ttb)
        return

    # The new interval overlaps with some existing intervals
    id_all = [intl.id for intl in intervals_to_merge]
    df_timetable = pd.DataFrame(TimetableRepo.fetch_by_multiple_interval_ids(db, id_all))
    df_merged = df_timetable.merge(df_ttb, how='outer', on=df_ttb.columns)  # perform outer join
    df_merged['interval_id'] = interval.id
    TimetableRepo.bulk_update_by_df(db, df_merged[df_merged['id'].notna()])  # update new interval id
    TimetableRepo.bulk_insert_by_df(db, df_merged[df_merged['id'].isna()])   # insert new records
    IntervalRepo.bulk_delete_by_id(db, id_all)  # finally remove all intervals that has been merged


def read_json_file(file: str) -> dict:
    """
    Read json int dict
    :param file: file path of the json data
    :return:
    """
    with open(file) as f:
        return json.load(f)


async def load_timetable(station: str, t0: int, db: Session):
    """
    Download timetables and store them into database
    :param station: station code
    :param t0: start timestamp of the timetable
    :param db: db session
    :return:
    """
    with tempfile.TemporaryDirectory() as tmp_dirname:
        downloaded_files = await download_multiple_timetables(station, t0, tmp_dirname)
        timetables = [parse_timetable(read_json_file(f)) for f in downloaded_files]
        df = pd.concat([df for df in timetables if df is not None], ignore_index=True).drop_duplicates()
        update_timetable(station, t0, df, db)
