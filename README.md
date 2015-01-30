Python Bundler
==============

_Python Bundler is to Python, as Bundler is to Ruby_

Simplifies virtualenv and pip usage.

No need to rewrite your `requirements.txt` when starting out.

Inspired by http://bundler.io/

Howto
-----
### For projects that are not using pbundle (yet)
* `easy_install pbundler` or `pip install pbundler`
* `cd` into your project path
* `pbundle init`

Already have a `requirements.txt`?
* `echo "pipspec()" >> ./Cheesefile`


### For projects already using pbundle
* `easy_install pbundler` or `pip install pbundler`
* cd into your project path
* `pbundle` It will install your project's dependencies into a fresh virtualenv.

To run commands with the activated virtualenv:

    pbundle exec bash -c 'echo "I am activated. virtualenv: $VIRTUAL_ENV"'


Or, for python programs:

    pbundle py ./debug.py


If you don't have a requirements.txt yet but have an existing project, try this:

    pip freeze > requirements.txt
    echo "pipspec()" >> ./Cheesefile


If you start fresh, try this for a project setup:

    mkdir myproject && cd myproject
    git init
    pbundle init


Instructions you can give your users:

    git clone git://github.com/you/yourproject.git
    easy_install pbundler
    pbundle


If you rather like pip, and you're sure your users already have pip:

    git clone git://github.com/you/yourproject.git
    pip install pbundler
    pbundle



Making python scripts automatically use pbundle py
--------------------------------------------------

Replace the shebang with "/usr/bin/env pbundle-py". Example:

    #!/usr/bin/env pbundle-py
    import sys
    print sys.path


WSGI/Unicorn example
--------------------

start-unicorn.sh:

    #!/bin/bash
    cd /srv/app/flaskr
    PYTHONPATH=/srv/app/wsgi exec pbundle exec gunicorn -w 5 -b 127.0.0.1:4000 -n flaskrprod flaskr:app


Custom environment variables
----------------------------

If you need to set custom ENV variables for the executed commands in your local copy, do this:

    echo "DJANGO_SETTINGS_MODULE='mysite.settings'" >> .pbundle/environment.py


TODO
----

* Build inventory from what is installed, instead of requirements.last file
* Handle failed egg installs
* Really remove all no longer needed packages from virtualenv
* Reorganize library code

