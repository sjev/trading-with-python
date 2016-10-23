
=======================
Getting data
=======================

Interactive Brokers historic data
===================================

Interactive Brokers provides *free* historic data (only for clients) up to 6 month in the past, with a maximum resolution 
of 1 second bars.  This is great of course, but to prevent abuse, IB imposed all kinds of download limitations.
You are not allowed to make more than 60 data requests per 10 minutes for example and the number of bars per request 
is limited.


The script ``tools/getData.py`` is designed to download large datasets while respecting the rules.

.. automodule:: getData


Interactive Brokers tick data
================================

.. automodule:: tickLogger






.. include:: yahooFinance.rst