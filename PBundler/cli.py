from __future__ import print_function

import os
import sys
import time
import traceback

from PBundler import PBundle

class PBCliError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


USAGE = """
pbundle                  Copyright 2012 Christian Hofstaedtler
pbundle Usage:
  pbundle [install]    - Run pip, if needed (also uninstalls removed
                         requirements)
  pbundle upgrade      - Run pip, with --upgrade
  pbundle init         - Create empty requirements.txt
  pbundle run program  - Run "program" in activated virtualenv
  pbundle py args      - Run activated python with args

To auto-enable your scripts, use "#!/usr/bin/env pbundle-py" as the
shebang line.

Website:      https://github.com/zeha/pbundler
Report bugs:  https://github.com/zeha/pbundler/issues
"""


class PBCli():
    def __init__(self):
        self._pb = None

    @property
    def pb(self):
        if not self._pb:
            basepath = PBundle.find_basepath()
            if not basepath:
                message = ("Could not find requirements.txt " +
                           "in path from here to root.")
                raise PBCliError(message)
            self._pb = PBundle(basepath)
        return self._pb

    def handle_args(self, argv):
        args = argv[1:]
        command = "install"
        if args:
            command = args.pop(0)
        if command in ['--help', '-h']:
            command = 'help'
        if 'cmd_' + command in PBCli.__dict__:
            return PBCli.__dict__['cmd_' + command](self, args)
        else:
            raise PBCliError("Unknown command \"%s\"" % (command,))

    def run(self, argv):
        try:
            return self.handle_args(argv)
        except PBCliError as e:
            print("E:", str(e))
            return 1
        except Exception as e:
            print("E: Internal error in pbundler:")
            print("  ", e)
            traceback.print_exc()
            return 120

    def cmd_help(self, args):
        print(USAGE.strip())

    def cmd_init(self, args):
        # can't use PBundle here
        if os.path.exists(REQUIREMENTS):
            raise PBCliError("Cowardly refusing, as %s already exists here." %
                             (REQUIREMENTS,))
        with open(REQUIREMENTS, "w") as f:
            f.write("# pbundle MAGIC\n")
            f.write("#pbundle>=0\n")
            f.write("\n")

    def cmd_install(self, args):
        if self.pb.requirements_changed():
            self.pb.uninstall_removed()
            self.pb.install()
            self.pb.save_requirements()

    def cmd_upgrade(self, args):
        self.pb.uninstall_removed()
        self.pb.upgrade()

    def cmd_run(self, args):
        return self.pb.run(args, verbose=False)

    def cmd_py(self, args):
        return self.pb.run(["python"] + args, verbose=False)
