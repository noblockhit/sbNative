import sys
sys.path.append(r"D:\AA_CODING\python\Projects\codebases\sbNative\src\sbNative")

import debugtools
import runtimetools


@debugtools.cleanRepr()
class someClass:
    someAttr = "hello"

someClass().log(runtimetools.getPath())