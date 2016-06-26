
from distutils.core import setup
import tradingWithPython as twp

# Work around mbcs bug in distutils.
# http://bugs.python.org/issue10945
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    ascii = codecs.lookup('ascii')
    func = lambda name, enc=ascii: {True: enc}.get(name=='mbcs')
    codecs.register(func)


 
setup(name = "tradingWithPython",
      version = twp.__version__,
      description = "A collection of functions and classes for Quantitative trading",
      author = "Jev Kuznetsov",
      author_email = "jev.kuznetsov@gmail.com",
      url = "http://www.tradingwithpython.com/",
      license = "BSD",
      packages=["tradingWithPython","tradingWithPython/lib","tradingWithPython/lib/interactiveBrokers"]
      )
