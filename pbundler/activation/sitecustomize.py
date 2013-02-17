from __future__ import print_function

import os
import traceback

try:
    import pbundler
    pbundler.PBundler.setup()
except:
    print("E: Exception in pbundler activation code.")
    print("")
    print("Please report this to the pbundler developers:")
    print("    http://github.com/zeha/pbundler/issues")
    print("")
    traceback.print_exc()
    print("")
