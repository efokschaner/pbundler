# minimal interpreter, mostly for debugging purposes.

from __future__ import print_function
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
    console = code.InteractiveConsole()
    console.interact("PBundler REPL on Python" + str(sys.version))
