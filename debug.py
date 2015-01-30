"""
A simple wrapper to invoke pbundler without needing to install it, making debugging easier in an IDE
"""
import sys

from pbundler import PBCli


def main():
    sys.exit(PBCli().run(sys.argv))


if __name__ == '__main__':
    main()