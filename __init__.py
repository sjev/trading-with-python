__docformat__ = 'restructuredtext'

# major , python ver, minor, bugfix
__version__ = '0.3.0.0'

import matplotlib.pyplot as plt
plt.style.use('ggplot')

from .lib import yahooFinance
from .lib import backtest