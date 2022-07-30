#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/30 16:00
# @Author  : liyun
# @desc    :
from pydantic import BaseModel


class Journey(BaseModel):
    summary: str
