#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
makefile for building documentation

@author: jev
"""

import os,sys,shutil
from os.path import join, exists,abspath,dirname

BUILD_DIR = 'build'

# init commands
INIT_GIT = """git push origin --delete gh-pages
git branch gh-pages
git checkout gh-pages
git symbolic-ref HEAD refs/heads/gh-pages
rm .git/index
git clean -fdx
touch .nojekyll
git add .nojekyll"""

GIT_NAME = 'trading-with-python'

# dict wih path locations
PATH = {'root':abspath(dirname(__file__))}
PATH['gh-pages'] = '../../gh-pages'

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def init():
    
    if not exists(PATH['gh-pages']):
        os.mkdir(PATH['gh-pages'])
    
    os.chdir(PATH['gh-pages'])
    
    if exists(GIT_NAME):
        shutil.rmtree(GIT_NAME)

    # clone
    os.system("git clone git@github.com:sjev/trading-with-python.git")
    
    os.chdir(GIT_NAME)
    
    for cmd in INIT_GIT.splitlines():
        print(cmd)
        os.system(cmd)
    
    os.chdir(PATH['root'])
    
def clean():
    if exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
        
    # create _static dir
    os.makedirs(os.path.join(BUILD_DIR,'html/_static'))
    
def html():
    print ("building html")
    os.system('sphinx-build -P -b html -d build/doctrees source build/html')

def commit():
    """ copy built docs to gh-pages and commit"""    
    dest = join(PATH['gh-pages'], GIT_NAME) 
    src = join(PATH['root'], 'build/html')
    os.chdir(dest)
    os.system('rm -rf *')
        
    print('Copying docs to:',dest)
    copytree(src,dest)
    os.system("git add *")
    os.system("git commit -am 'autopublish'")
    
    os.system("git push -u origin gh-pages")
    os.chdir(PATH['root'])
    
if __name__ == "__main__":
    # functional mapping
    funcd = {'clean':[clean],
             'html':[html],
             'init':[init],
             'commit':[commit]}
    
    if len(sys.argv) == 1 :
        arg = 'html' # default action
    else:
        arg = sys.argv[1]

    for f in funcd[arg]:
        f()