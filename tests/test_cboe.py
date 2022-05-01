#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test cboe download

@author: jev
"""

import pytest

import tradingWithPython.lib.cboe as cboe
import pandas as pd
import numpy as np


@pytest.mark.skip(reason="takes too long")
def test_histData():
    """test automatic download of csv data from CBOE"""

    data = cboe.getHistoricData()


def test_expiration():
    """test expiration dates of a future"""

    now = pd.Timestamp("2018-01-01")

    fut = cboe.VixFuture(2018, 1)
    assert fut.expirationDate == pd.Timestamp("2018-01-17")

    # NYSE closed on Jan 1, 15 - should be 10 trading days left
    ttl = fut.ttl(now)
    assert ttl == 10
