import sys,os
import inspect
import pathlib

def getPath():
    if sys.executable.endswith("python.exe"):
        return pathlib.Path(os.path.dirname(os.path.realpath(__file__).replace("\\","/").replace("engine", "")))
    else:
        return pathlib.Path(sys.executable.replace(sys.executable.split("\\")[-1],"").replace("\\","/")[:-1])


def globaliseAllSubitems(destFileGlobals,packageToUnpack,forceall=False):
    for name,g in inspect.getmembers(packageToUnpack):
        if not forceall and name.startswith("_"):continue
        destFileGlobals[name] = g