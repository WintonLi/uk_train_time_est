#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 20:00
# @Author  : liyun
# @desc    :
from pydantic import BaseSettings, Field, RedisDsn


class Settings(BaseSettings):
    env: str = Field("develop", env="ENV")
    server_port: int = Field(9000, env='SERVER_PORT')
    tpt_url: str = Field("https://transportapi.com/v3/uk/train/station", env="TPT_URL")
    tpt_app_id: str = Field("", env="TPT_APP_ID")
    tpt_app_key: str = Field("", env="TPT_APP_KEY")
    tz: str = Field("Europe/London", env="TZ")
    db_url: str = Field("sqlite:///./train.db", env="DB_URL")
    ub_max_waiting: int = Field(180, env="UB_MAX_WAITING")  # upper boundary of max waiting, in minutes
    max_single_journey: int = Field(3600*4, env="MAX_SINGLE_JOURNEY")  # longest single journey to consider, in seconds
    t_window: int = Field(2, env="T_WINDOW")  # time window of a single downloaded timetable
    download_concurrency: int = Field(3, env="DOWNLOAD_CONCURRENCY")  # how many API calls are run when downloading

    class Config:
        env_file = '.env'  # variables in this file have higher priorities


settings = Settings()
if not settings.tpt_app_id or not settings.tpt_app_key:
    raise ValueError('Key and/or app id for transport api are/is missing.')
