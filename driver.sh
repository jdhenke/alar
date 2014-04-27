#!/bin/sh

./node_modules/.bin/grunt --gruntfile celestrium/Gruntfile.coffee &&
./node_modules/.bin/grunt &&
source env/bin/activate &&
pecan serve config.py
