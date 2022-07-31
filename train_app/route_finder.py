#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 16:50
# @Author  : liyun
# @desc    :
from typing import List
from sqlalchemy.orm import Session
from models import Timetable
from schemas import SingleJourney
import pandas as pd
from settings import settings
from repositories import IntervalRepo, TimetableRepo
from etl import load_timetable


class RouteFinder:
    def __init__(self, db: Session):
        self.db = db

    def get_saved_timetable(self, station: str, t0: int) -> pd.DataFrame or None:
        """
        Get timetable data already saved in the db
        :param station: station code
        :param t0: the time of interest
        :return: timetable data, or None if data not previously saved
        """
        interval = IntervalRepo.fetch_including(self.db, station, t0)
        if interval is None:
            return None
        return pd.DataFrame(TimetableRepo.fetch_by_interval_id(self.db, interval.id))


    async def search_routes(self, stations: List[str], start_time: int, max_waiting: int) -> List[SingleJourney]:
        """
        Search the optimal routes connecting the given list of stations
        :param stations: a list of station codes
        :param start_time: timestamp of the start time
        :param max_waiting: the maximum time the passenger is willing to wait (in minutes)
        :return: the arrival timestamp
        """
        res = []  # contains individual routes from the start to end stations
        t_dept = start_time  # ideal departure time of passenger
        for i in range(len(stations) - 1):
            dept_station, target_station = stations[i:i + 2]
            df_dept, dept_downloaded = await self.get_timetable(dept_station, t_dept)
            df_target, target_downloaded = await self.get_timetable(target_station, t_dept)
            route = self.find_single_route(df_dept, df_target, t_dept)
            if route is None:
                if dept_downloaded and target_downloaded:
                    raise NotImplementedError(f'Unable to find a route between {dept_station} and {target_station}')
                if not dept_downloaded:
                    await load_timetable(dept_station, t_dept, self.db)  # try to load more data
                    df_dept, dept_downloaded = await self.get_timetable(dept_station, t_dept)
                if not target_downloaded:
                    await load_timetable(target_station, t_dept, self.db)
                    df_target, target_downloaded = await self.get_timetable(target_station, t_dept)
            route = self.find_single_route(df_dept, df_target, t_dept)  # retry with more data
            if route.departure_timestamp - start_time > max_waiting:
                raise ValueError('Wait time too long')
            t_dept = route.arrival_timestamp
            res.append(route)
        return res

    @staticmethod
    def find_single_route(dept_ttb: pd.DataFrame,
                          target_ttb: pd.DataFrame,
                          dept_station: str,
                          target_station: str,
                          t_dept: int) -> SingleJourney or None:
        """
        Find the fastest route connecting departure and target stations
        :param dept_ttb: the timetable of the departure station
        :param target_ttb: the timetable of the target station
        :param dept_station: code of the departure station
        :param target_station: code of the target station
        :param t_dept: departing time
        :return: the fastest route, or None
        """
        df_merged = dept_ttb.merge(target_ttb, how='inner', on='train_uid', suffixes=('_d', '_a'))
        if not len(df_merged):  # no train connection
            return None
        best_route = df_merged.sort_values('aimed_arrival_timestamp_a').iloc[0]
        return SingleJourney.parse_obj({
            'train_uid': best_route['train_uid_a'],
            'departure_station': dept_station,
            'destination_station': target_station,
            'departure_timestamp': best_route['departure_timestamp_a'],
            'arrival_timestamp': best_route['arrival_timestamp_a']
        })

    async def get_timetable(self, station: str, t0: int) -> (pd.DataFrame, bool):
        """
        Load **CONTIGUOUS** timetable data from db i.e data sharing the same window_id, given t0 and t1
        :param station: station code
        :param t0: the start timestamp of the timetable
        :return: the dataframe, and a variable indicating whether data has been downloaded
        """
        df = self.get_saved_timetable(station, t0)
        if df is not None:
            return df, False

        await load_timetable(station, t0, self.db)
        df = self.get_saved_timetable(station, t0)
        if df is None:
            raise RuntimeError('Unable to get data from API server')
        return df, True


