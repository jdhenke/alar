#!/bin/sh

grunt --gruntfile celestrium/Gruntfile.coffee &&
grunt &&
source env/bin/activate &&
pecan serve config.py
