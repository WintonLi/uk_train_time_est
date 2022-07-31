#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 16:00
# @Author  : liyun
# @desc    :
from typing import List
from pydantic import BaseModel


class SingleJourneyBase(BaseModel):
    train_id: str
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
