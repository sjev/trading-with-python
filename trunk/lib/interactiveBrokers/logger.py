#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# Defines logging formats and logger instance
##

import logging
import os

##
# Default log message formatting string.
format = '%(asctime)s %(levelname)s [%(name)s]  %(message)s'

##
# Default log date formatting string.
datefmt = '%d-%b-%y %H:%M:%S'

##
# Default log level.  Set TWP_LOGLEVEL environment variable to
# change this default.
level = int(os.environ.get('TWP_LOGLEVEL', logging.DEBUG))


def getLogger(name='twp', level=level, format=format,
               datefmt=datefmt):
    """ Configures and returns a logging instance.

    @param name ignored
    @param level logging level
    @param format format string for log messages
    @param datefmt format string for log dates
    @return logging instance (the module)
    """
	#print 'Loglevel:' , level
    logging.basicConfig(level=level, format=format, datefmt=datefmt)
    return logging.getLogger(name)
