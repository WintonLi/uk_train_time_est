#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 10:46
# @Author  : liyun
# @desc    :
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base, APPTZ


class Timetable(Base):
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, index=True)
    station_code = Column(String(3), nullable=False)
    window_id = Column(Integer)
    service = Column(Integer)
    train_uid = Column(String(20), nullable=False)
    aimed_departure_timestamp = Column(Integer)
    aimed_arrival_timestamp = Column(Integer)

    def __repr__(self):
        return f'{self.station_code} {self.train_uid} {datetime.fromtimestamp(self.aimed_arrival_timestamp, tz=APPTZ)}'


