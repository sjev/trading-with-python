from setuptools import setup, find_packages
import twp

setup(
    name="twp",
    version=twp.__version__,
    description="A collection of functions and classes for Quantitative trading",
    author="Jev Kuznetsov",
    author_email="jev.kuznetsov@gmail.com",
    url="https://github.com/sjev/trading-with-python",
    license="BSD",
    packages=[
        "twp",
    ],
)
