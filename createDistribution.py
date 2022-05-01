# -*- coding: utf-8 -*-


import os, shutil


def copyFiles(sourceDir, targetDir, includes=None):

    print(("Copy %s -> %s" % (sourceDir, targetDir)))
    if not os.path.exists(targetDir):
        print(("Creating ", targetDir))
        os.makedirs(targetDir)

    for f in os.listdir(sourceDir):

        base, ext = os.path.splitext(f)

        if (ext == ".py") and (True if not includes else (base in includes)):
            s = os.path.join(sourceDir, f)
            d = os.path.join(targetDir, f)
            print((s, "->", d))
            shutil.copyfile(s, d)


sourceDir = "lib"
targetDir = "dist/tradingWithPython/lib"
includes = [
    "__init__",
    "cboe",
    "csvDatabase",
    "functions",
    "yahooFinance",
    "extra",
    "bats",
    "backtest",
    "plotting",
    "calendar",
]

DEST = "dist/tradingWithPython"

try:
    shutil.rmtree(DEST)
except:
    pass

os.makedirs(DEST)  # create target dir

print("-----------init file---------")
shutil.copyfile("__init__.py", os.path.join(DEST, "__init__.py"))
print("-----------lib files---------")
copyFiles(sourceDir, targetDir, includes)
print("-----------IB files----------")
copyFiles(sourceDir + "/interactiveBrokers", targetDir + "/interactiveBrokers")
print("-----------data files -------")
os.mkdir("dist/tradingWithPython/lib/data")
shutil.copyfile(
    "lib/data/vix_expiration.txt", os.path.join(DEST, "lib/data/vix_expiration.txt")
)
