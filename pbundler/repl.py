from __future__ import print_function
from __future__ import absolute_import

__all__ = ['run']

import PBundler
import traceback
import sys
import code
import rlcompleter
import readline
readline.parse_and_bind("tab: complete")

# readline magically hooks into code.InteractiveConsole somehow.
# don't ask.


def run():
    """minimal interpreter, mostly for debugging purposes."""

    console = code.InteractiveConsole()
    console.interact("PBundler REPL on Python" + str(sys.version))
