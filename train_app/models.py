#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 10:46
# @Author  : liyun
# @desc    :
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base, APPTZ


class Interval(Base):
    __tablename__ = "intervals"
    id = Column(Integer, primary_key=True, index=True)
    start_timestamp = Column(Integer)
    stop_timestamp = Column(Integer)
    items = relationship("Timetable", primaryjoin="Interval.id == Timetable.interval_id", cascade="all, delete")


class Timetable(Base):
    __tablename__ = "timetables"

    id = Column(Integer, primary_key=True, index=True)
    station_code = Column(String(3), nullable=False)
    service = Column(Integer)
    train_uid = Column(String(20), nullable=False)
    aimed_departure_timestamp = Column(Integer)
    aimed_arrival_timestamp = Column(Integer)
    interval_id = Column(Integer, ForeignKey('intervals.id'), nullable=False)

    def __repr__(self):
        return f'{self.station_code} {self.train_uid} {datetime.fromtimestamp(self.aimed_arrival_timestamp, tz=APPTZ)}'


