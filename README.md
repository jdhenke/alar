Alar
======

> Local web interface to understand inference over custom knowledgebases.

## Setup

Here's how to get the software, setup an existing or custom KB then access the interface.

### Installation

Make you sure have virtualenv, npm and node installed.

Additionally, I've found it easier to install numpy and scipy globally and include system site packages in my virtualenv.

> Here's my current setup on Mac OS X 10.9.2 for reference.
>
>     $ npm --version
>     1.2.17
>     $ virtualenv --version
>     1.10.1
>     $ node --version
>     v0.10.3
>     $ python -c "import numpy; print numpy.version.version"
>     1.8.1
>     $ python -c "import scipy; print scipy.version.version"
>     0.14.0rc1


Download this repo and install its dependencies.

```bash
# get the code
git clone --recursive https://github.com/jdhenke/alar.git
cd alar

# install npm dependencies
npm install
(cd celestrium && npm install)
sudo npm install -g grunt-cli

# install python dependencies
virtualenv env --system-site-packages
source env/bin/activate
pip install pecan
python setup.py develop
```

### Setting up a KB

To use your own KB, put it in a CSV file with each row being 3 cells of
`concept, relation, concept`. You can get C4's assertion list with the following.

```bash
curl http://mit.edu/jdhenke/www/alar/assertions.csv > assertions.csv
```

Then, to prep your KB, run the following.

```bash
source env/bin/activate
python prep_kb.py assertions.csv
```

> TODO: This CSV was generated using get-c4-assertions repo.

### Running

Once your KB has been prepped, run `. driver` from inside the repo and go to [http://localhost:8080/](http://localhost:8080/).

## Using the Interface

See this [illustrated tutorial of Alar](https://docs.google.com/document/d/19KUwApiWCTEXaLUh_mrC_aCe-1VazFbHiaaFxZ6ImAo/edit?usp=sharing).

![image](https://cloud.githubusercontent.com/assets/1418690/2674280/aeb1a960-c0fe-11e3-9867-49b8a3292729.png)
