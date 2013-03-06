Python Bundler
==============

The easiest way to manage your Python application's dependencies.

Inspired by http://gembundler.com/


Quickstart
----------

Managing dependencies with pbundler is easy. Install pbundler on your machine:

    $ easy_install pbundler


Then, in your project root, specify the dependencies:

    $ pbundle init
    $ vim Cheesefile

Example Cheesefile:

```python
source("pypi")
pkg("Pillow")
pkg("Flask", ">=0.8")
```


Now install all your dependencies:

    $ pbundle install
    $ git add Cheesefile Cheesefile.lock


Inside your app, load the environment:

```python
import pbundler
pbundler.PBundler.setup()

# import your dependencies as usual
import Flask
```


Run a commands with the activated packages:

    $ pbundle exec ./server.py


Or, to get a Python shell:

    $ pbundle console

(If you have IPython in your Cheesefile, it will be an IPython shell.)


Instructions for your users
---------------------------


    $ git clone git://github.com/you/yourproject.git && cd yourproject
    $ easy_install pbundler
    $ pbundle


TODO
----

* Lots of things!
