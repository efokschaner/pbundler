from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import time
import traceback
import sys

import pbundler

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
        self._bundle = None


    @property
    def bundle(self):
        if not self._bundle:
            self._bundle = pbundler.PBundler.load_bundle()
        return self._bundle


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
            raise pbundler.PBundlerException("Unknown command \"%s\"" % (command,))

    def run(self, argv):
        try:
            return self.handle_args(argv)
        except pbundler.PBundlerException as e:
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
        self.bundle.install(['default'])

    def cmd_upgrade(self, args):
        self.bundle.upgrade()

    def cmd_run(self, args):
        #self.bundle.validate_requirements()
        return self.bundle.run(args, verbose=False)

    def cmd_py(self, args):
        #self.bundle.validate_requirements()
        return self.bundle.run(["python", "-S"] + args, verbose=False)

    def cmd_repl(self, args):
        #self.bundle.validate_requirements()
        import pbundler.repl
        pbundler.repl.run()


def pbcli():
    sys.exit(PBCli().run(sys.argv))


def pbpy():
    argv = [sys.argv[0], "py"] + sys.argv[1:]
    sys.exit(PBCli().run(argv))
