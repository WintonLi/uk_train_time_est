#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 16:00
# @Author  : liyun
# @desc    :
from typing import List
from pydantic import BaseModel


class TimetableBase(BaseModel):
    service: int
    train_uid: str
    aimed_departure_timestamp: int
    aimed_arrival_timestamp: int
    interval_id: int


class TimetableCreate(TimetableBase):
    pass


class TimetableObj(TimetableBase):
    id: int

    class Config:
        orm_mode = True


class IntervalBase(BaseModel):
    station_code: str
    start_timestamp: int
    stop_timestamp: int


class IntervalCreate(IntervalBase):
    pass


class IntervalObj(IntervalBase):
    id: int
    timetables: List[TimetableBase]

    class Config:
        orm_mode = True


class SingleJourneyBase(BaseModel):
    train_uid: str
    departure_station: str
    destination_station: str


class SingleJourney(SingleJourneyBase):
    departure_timestamp: int
    arrival_timestamp: int


class SingleJourneyOutput(SingleJourneyBase):
    departure_time: str
    arrival_time: str


class Journey(BaseModel):
    summary: str
    routes: List[SingleJourneyOutput]
