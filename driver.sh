#!/bin/sh

grunt --gruntfile celestrium/Gruntfile.coffee &&
grunt &&
source env/bin/activate &&
python server/server.py
