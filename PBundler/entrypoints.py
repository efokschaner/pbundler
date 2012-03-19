from PBundler import PBCli
import sys


def pbcli():
    sys.exit(PBCli().run(sys.argv))


def pbpy():
    argv = [sys.argv[0], "py"] + sys.argv[1:]
    sys.exit(PBCli().run(argv))
