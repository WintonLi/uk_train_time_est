#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/31 10:13
# @Author  : liyun
# @desc    :
from typing import List
import pandas as pd
from models import Interval, Timetable
from sqlalchemy.orm import Session
from sqlalchemy import delete
from schemas import IntervalCreate, TimetableCreate


class IntervalRepo:
    @staticmethod
    def create(db: Session, interval: IntervalCreate):
        db_interval = Interval(station_code=interval.station_code, start_timestamp=interval.start_timestamp,
                               stop_timestamp=interval.stop_timestamp)
        db.add(db_interval)
        db.commit()
        db.refresh(db_interval)
        return db_interval

    @staticmethod
    def fetch_all(db: Session):
        return db.query(Interval).all()

    @staticmethod
    def fetch_by_station(db: Session, station: str):
        return db.query(Interval).filter(Interval.station_code == station)

    @classmethod
    def fetch_including(cls, db: Session, station: str, val: int) -> Interval or None:
        """
        Return the interval that includes the value.
        :param db: database session
        :param station: Station code
        :param val: the value in the interval
        :return:
        """
        return cls.fetch_by_station(db, station)\
            .filter(Interval.start_timestamp < val, Interval.stop_timestamp >= val).first()

    @classmethod
    def fetch_included(cls, db: Session, station: str, min_val: int, max_val: int):
        """
        Return all intervals that are within the range specified by min_val and max_val
        :param db: database session
        :param station: station code
        :param min_val: min value
        :param max_val: max value
        :return: all intervals
        """
        return cls.fetch_by_station(db, station)\
            .filter(Interval.start_timestamp > min_val, Interval.stop_timestamp <= max_val)

    @staticmethod
    def update(db: Session, interval_data):
        updated_interval = db.merge(interval_data)
        db.commit()
        return updated_interval

    @staticmethod
    def bulk_delete_by_id(db: Session, ids: List[int]):
        db.execute(delete(Interval).where(Interval.id.in_(ids)))


class TimetableRepo:
    @staticmethod
    def make_timetable(ttb: TimetableCreate) -> Timetable:
        return Timetable(
            service=ttb.service, train_uid=ttb.train_uid, aimed_departure_timestamp=ttb.aimed_departure_timestamp,
            aimed_arrival_timestamp=ttb.aimed_arrival_timestamp, interval_id=ttb.interval_id)

    @staticmethod
    def make_ttb_dicts_by_df(df_ttb: pd.DataFrame, include_id: bool) -> List[dict]:
        """
        Make a list of timetable dictionary by a pandas dataframe
        :param df_ttb: the dataframe
        :param include_id: whether id is included in the dicts
        :return: the list of dicts
        """
        cols = ['service', 'train_uid', 'aimed_departure_timestamp', 'aimed_arrival_timestamp', 'interval_id']
        if include_id:
            cols.append('id')
        return df_ttb[cols].to_dict(orient='records')

    @classmethod
    def create(cls, db: Session, ttb: TimetableCreate):
        db_timetable = cls.make_timetable(ttb)
        db.add(db_timetable)
        db.commit()
        db.refresh(db_timetable)
        return db_timetable

    @classmethod
    def bulk_insert_by_df(cls, db: Session, df_ttb: pd.DataFrame):
        db.bulk_save_objects([Timetable(**ttb) for ttb in cls.make_ttb_dicts_by_df(df_ttb, include_id=False)])

    @classmethod
    def bulk_update_by_df(cls, db: Session, df_ttb: pd.DataFrame):
        db.bulk_update_mappings(Timetable, cls.make_ttb_dicts_by_df(df_ttb, include_id=True))

    @staticmethod
    def fetch_by_interval_id(db: Session, interval_id: int):
        return db.query(Timetable).filter(Timetable.interval_id == interval_id)

    @staticmethod
    def fetch_by_multiple_interval_ids(db: Session, ids: List[int]):
        return db.query(Timetable).filter(Timetable.interval_id.in_(ids)).all()
