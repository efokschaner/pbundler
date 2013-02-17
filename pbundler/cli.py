from __future__ import print_function
from __future__ import absolute_import

__all__ = ['PBCli', 'pbcli', 'pbpy']

import os
import sys
import time
import traceback

import pbundler


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
        if command == '--version':
            command = 'version'
        if 'cmd_' + command in PBCli.__dict__:
            return PBCli.__dict__['cmd_' + command](self, args)
        else:
            raise pbundler.PBundlerException("Could not find command \"%s\"." %
                                             (command,))

    def run(self, argv):
        try:
            return self.handle_args(argv)
        except pbundler.PBundlerException as ex:
            print("E:", str(ex))
            return 1
        except Exception as ex:
            print("E: Internal error in pbundler:")
            print("  ", ex)
            traceback.print_exc()
            return 120

    def cmd_help(self, args):
        print(USAGE.strip())

    def cmd_init(self, args):
        path = os.getcwd()
        if len(args) > 0:
            path = os.path.abspath(args[0])
        pbundler.cheesefile.Cheesefile.generate_empty_file(path)

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

    def cmd_version(self, args):
        import pkg_resources
        dist = pkg_resources.get_distribution('pbundler')
        print(dist)
        return 0


def pbcli():
    sys.exit(PBCli().run(sys.argv))


def pbpy():
    argv = [sys.argv[0], "py"] + sys.argv[1:]
    sys.exit(PBCli().run(argv))
