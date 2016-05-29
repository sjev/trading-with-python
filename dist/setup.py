from distutils.core import setup
 
import tradingWithPython as twp

 
setup(name = "tradingWithPython",
      version = twp.__version__,
      description = "A collection of functions and classes for Quantitative trading",
      author = "Jev Kuznetsov",
      author_email = "jev.kuznetsov@gmail.com",
      url = "http://www.tradingwithpython.com/",
      license = "BSD",
      packages=["tradingWithPython","tradingWithPython/lib","tradingWithPython/lib/interactiveBrokers"]
      )