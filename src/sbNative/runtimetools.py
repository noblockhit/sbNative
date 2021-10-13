import sys,os
import inspect
import pathlib
import traceback
import typing
import types

def getPath():
    if sys.executable.endswith("python.exe"):
        fl = inspect.stack()[1].filename
        return pathlib.Path(os.path.dirname(os.path.realpath(fl).replace("\\","/").replace("engine", "")))
    else:
        return pathlib.Path(sys.executable.replace(sys.executable.split("\\")[-1],"").replace("\\","/")[:-1])


def globaliseAllSubitems(destFileGlobals,packageToUnpack,forceall=False):
    for name,g in inspect.getmembers(packageToUnpack):
        if not forceall and name.startswith("_"):continue
        destFileGlobals[name] = g

class InterpreterError(Exception):pass

def execWithExcTb(cmd, globals=None, locals=None, description='source string'):
    try:
        exec(cmd, globals, locals)
    except SyntaxError as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        line_number = err.lineno
    except Exception as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        cl, exc, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1][1]
    else:
        return
    raise InterpreterError("%s at line %d of %s: %s" % (error_class, line_number, description, detail))

def safeIter(itr: typing.Sequence) -> types.GeneratorType:
    '''Warning, very slow with large iterators.'''
    i = 0
    while i < len(itr):
        item = itr[i]
        yield item
        if len(itr) <= i or itr[i] == item:
            i += 1