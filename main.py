#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 10:42
# @Author  : liyun
# @desc    :
import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from datetime import datetime
from train_app.shcemas import Journey
import train_app.models as models
from db import get_db, engine


app = FastAPI(title="Timetable FastAPI Application",
              description="FastAPI Application that finds the arrival time of a route given a start time",
              version="1.0.0", )

models.Base.metadata.create_all(bind=engine)


@app.get('/arrival_time', response_model=Journey)
def get_arrival_time(stations: str, date: str, start_time: str, db: Session = Depends(get_db)):
    """
    Return arrival time of a route
    """
    station_list = [s.strip() for s in stations.split(',')]
    start_timestamp = datetime.strptime(f'{date} {start_time}', '%Y-%m-%d %H:%M').timestamp()
    return {'summary': '13.25'}


if __name__ == "__main__":
    uvicorn.run("main:app", port=9000, reload=True)
