# -*- coding: utf-8 -*-
"""
Convenience module for creating loggers

@author: Jev Kuznetsov
"""

import logging


# configure logging
# create logger


def getLogger(name, logFile=None, consoleLevel=logging.INFO):
    """configure top level logging"""

    logging.basicConfig(
        level=logging.DEBUG,
        filename=logFile,
        filemode="w",
        format="%(asctime)s [%(name)s-%(funcName)s] - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    # create stream log handler
    console = logging.StreamHandler()
    console.setLevel(consoleLevel)
    formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)  # add the handler to the root logger

    return log
