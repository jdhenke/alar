Apollo
======

A tool to visualize inference over semantic networks.

Installing
==========

Requires [node](http://nodejs.org/) and [virtualenv](http://bit.ly/1a8k2eo).

```bash

git clone --recursive https://github.com/jdhenke/apollo.git
cd apollo
npm install
(cd celestrium && npm install)
virtualenv env
source env/bin/activate
pip install numpy cherrypy networkx simplejson
pip install divisi2 csc-pysparse csc-utils

```

Running
=======

```bash

. driver.sh

```

The interface can be found at [http://localhost:8765/](http://localhost:8765/).

Interface Tutorial
==================

> # TODO
