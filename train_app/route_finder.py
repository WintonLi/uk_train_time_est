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


class RouteFinder:
    def __init__(self, db: Session):
        self.db = db

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
        ub_waiting = min(max_waiting, settings.ub_max_waiting)  # limit the max waiting minutes to avoid api abusing
        for i in range(len(stations) - 1):
            dept_station, target_station = stations[i:i + 2]
            t_dept_max = t_dept + ub_waiting * 60  # maximum departure time of passenger (can't wait too long)
            t_arri_max = t_dept_max + settings.max_single_journey
            df_dept = await self.get_timetable(dept_station, t_dept, t_dept_max)  # timetable of the departure station
            df_target = await self.get_timetable(target_station, t_dept, t_arri_max)  # timetable of the target station
            opt_journey = self.find_single_route(df_dept, df_target)
            t_dept = opt_journey.arrival_timestamp
            res.append(opt_journey)
        return res

    def find_single_route(self, dept_station: str, target_station: str, t_dept: int) -> SingleJourney:
        """
        Find the fastest route connecting departure and target stations
        :param dept_station: the code of the departure station
        :param target_station: the code of the target station
        :param t_dept: departing time
        :return: the fastest route
        """

    async def get_timetable(self, station: str, t0: int, t1: int, is_dept: bool) -> pd.DataFrame:
        """
        Load **CONTIGUOUS** timetable data from db i.e data sharing the same window_id, given t0 and t1
        :param station: station code
        :param t0: the start timestamp of the timetable
        :param t1: the stop timestamp of the timetable
        :param is_dept: whether the station of interest is a departure station
        :return:
        """
        tb = self.db.query(Timetable).filter(
            Timetable.station_code == station,
            Timetable.aimed_departure_timestamp if is_dept else Timetable.aimed_arrival_timestamp >= t0,
            Timetable.aimed_departure_timestamp if is_dept else Timetable.aimed_arrival_timestamp <= t1)
        if not len(tb):

        df = pd.DataFrame(tb)\
            .sort_values(by='aimed_departure_timestamp' if is_dept else 'aimed_arrival_timestamp', ascending=False)



