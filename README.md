Alar
======

> Local web interface to understand inference over custom knowledgebases.

**First** - ensure [node](http://nodejs.org/) and [virtualenv](https://pypi.python.org/pypi/virtualenv) are installed.

**Second** - execute the following...

```bash
# get the code
git clone --recursive https://github.com/jdhenke/alar.git
cd alar

# install dependencies
npm install
(cd celestrium && npm install)
virtualenv env
source env/bin/activate
pip install numpy matplotlib networkx pecan watchdog
pip install csc-pysparse csc-utils divisi2

# setup pecan
python setup.py develop

# run the server
. driver.sh
```

**Third** - go to [http://localhost:8080/](http://localhost:8080/).
